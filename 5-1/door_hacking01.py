#!/usr/bin/env python3
# advanced_safe_pipeline_v2.py
# 안전 학습용 후보 파이프라인 (오류 수정 + 패턴 출력/덤프/프로파일)
#
# - 절대 암호 해제 시도 없음. simulate (sha256 비교) / noop 모드만 지원.
# - 추가 기능:
#   * --dump-candidates PATH : producer가 생성한 후보를 스트리밍으로 파일에 append
#   * --profile {conservative,balanced,aggressive} : score 가중치 프리셋
#   * --pw-weight/--pcfg-weight/--markov-weight ... : 개별 가중치 override 가능
#   * 상위 패턴 출력 및 간단 텍스트 바 시각화 (stdout)
#
# 추가 반영:
# - password.txt에 찾은 암호 저장 (문제1)
# - --interactive-position 옵션: 찾았을 때 사용자에게 "몇번째 자리 식별?" 묻고 result.txt에 기록 (문제2)
# - --stop-on-dict-match 옵션: 생성된 후보에 wordlist의 단어가 포함되면 즉시 중단 (보너스)
#
# 안전 주의: 실제 ZIP 추출/해제는 수행하지 않음. simulate 모드는 sha256 비교로만 동작.

import argparse
import multiprocessing as mp
import time
import hashlib
import random
import itertools
import os
import sys
import math
import heapq
import json
from collections import defaultdict, Counter
from typing import Iterable, List, Tuple, Optional, Any

CHARSET = '0123456789abcdefghijklmnopqrstuvwxyz'
DEFAULT_LENGTH = 6


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def atomic_write_json(path: str, obj: Any):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def run_benchmark(workers: int = None, duration: float = 5.0, length: int = DEFAULT_LENGTH):
    if workers is None:
        try:
            workers = min(8, mp.cpu_count())
        except Exception:
            workers = 8
    manager = mp.Manager()
    return_dict = manager.dict()

    def _bench_worker(wid, dur, charset, length, ret):
        rnd = random.Random(wid + int(time.time()))
        end = time.time() + dur
        cnt = 0
        _choice = rnd.choice
        _sha256 = hashlib.sha256
        while time.time() < end:
            s = ''.join(_choice(charset) for _ in range(length))
            _sha256(s.encode()).digest()
            cnt += 1
        ret[wid] = cnt

    procs = []
    start = time.time()
    for wid in range(workers):
        p = mp.Process(target=_bench_worker, args=(wid, duration, CHARSET, length, return_dict))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
    elapsed = time.time() - start
    counts = [return_dict.get(i, 0) for i in range(workers)]
    total = sum(counts)
    ops_per_sec = total / elapsed if elapsed > 0 else 0.0
    keyspace = 36 ** length
    est_seconds = keyspace / ops_per_sec if ops_per_sec > 0 else float('inf')
    return {
        'workers': workers,
        'counts': counts,
        'total': total,
        'elapsed': elapsed,
        'ops_per_sec': ops_per_sec,
        'keyspace': keyspace,
        'est_seconds': est_seconds
    }


def load_wordlist(path: str, max_words: Optional[int] = None) -> List[str]:
    out: List[str] = []
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                w = ''.join(ch for ch in line.strip().lower() if ch.isalnum())
                if w:
                    out.append(w)
                if max_words and len(out) >= max_words:
                    break
    except FileNotFoundError:
        return []
    return out


def build_freq_map(words: Iterable[str]) -> Counter:
    return Counter(words)


def mangling_variants(word: str) -> Iterable[str]:
    s = word.lower()
    variants = set([s])
    for d2 in itertools.product('0123456789', repeat=2):
        variants.add(s + ''.join(d2))
    for d4 in itertools.product('0123456789', repeat=4):
        variants.add(s + ''.join(d4))
    for d in '0123456789':
        variants.add(d + s)
    leet = {'o': '0', 'i': '1', 's': '5', 'a': '4', 'e': '3', 'l': '1'}
    sl = list(s)
    for i, ch in enumerate(sl):
        if ch in leet:
            t = sl.copy()
            t[i] = leet[ch]
            variants.add(''.join(t))
    out = set()
    for v in variants:
        if len(v) == DEFAULT_LENGTH:
            out.add(v)
        elif len(v) < DEFAULT_LENGTH:
            out.add(v + '0' * (DEFAULT_LENGTH - len(v)))
        else:
            out.add(v[:DEFAULT_LENGTH])
    return out


def train_markov(wordlist: Iterable[str], order: int = 2):
    counts = defaultdict(Counter)
    for w in wordlist:
        token = '^' + w + '$'
        for i in range(len(token) - (order - 1)):
            hist = token[i:i + order - 1]
            nxt = token[i + order - 1]
            counts[hist][nxt] += 1
    model = {}
    for hist, ctr in counts.items():
        total = sum(ctr.values())
        items = []
        cum = 0.0
        for ch, c in ctr.items():
            cum += c / total
            items.append((cum, ch))
        model[hist] = items
    return model


def sample_markov(model, length: int = DEFAULT_LENGTH, order: int = 2, rnd: Optional[random.Random] = None):
    if rnd is None:
        rnd = random.Random()
    res = ''
    history = '^' * (order - 1)
    while len(res) < length:
        items = model.get(history)
        if not items:
            ch = rnd.choice(CHARSET)
        else:
            r = rnd.random()
            ch = items[0][1]
            for cum, c in items:
                if r <= cum:
                    ch = c
                    break
        if ch == '$':
            continue
        res += ch
        history = (history + ch)[-(order - 1):]
    return res[:length]


def token_pattern_from_candidate(s: str) -> Tuple[str, List[str]]:
    tokens: List[str] = []
    buf = s[0]
    for ch in s[1:]:
        if (ch.isdigit() and buf[-1].isdigit()) or (ch.isalpha() and buf[-1].isalpha()):
            buf += ch
        else:
            tokens.append(buf)
            buf = ch
    tokens.append(buf)
    pattern = ' '.join('W' if t[0].isalpha() else 'D' for t in tokens)
    return pattern, tokens


def train_pcfg_from_wordlist(wordlist: Iterable[str], max_patterns: Optional[int] = None) -> List[Tuple[str, float]]:
    pattern_counts: Counter = Counter()
    for w in wordlist:
        w_clean = ''.join(ch for ch in w if ch.isalnum())
        cand_set = set()
        cand_set.add(w_clean)
        for v in mangling_variants(w_clean):
            cand_set.add(v)
        for cand in cand_set:
            pat, _ = token_pattern_from_candidate(cand)
            pattern_counts[pat] += 1
    total = sum(pattern_counts.values()) or 1
    pattern_probs = [(pat, cnt / total) for pat, cnt in pattern_counts.items()]
    pattern_probs.sort(key=lambda x: x[1], reverse=True)
    if max_patterns:
        pattern_probs = pattern_probs[:max_patterns]
    return pattern_probs


def sample_from_pcfg(pattern_probs: List[Tuple[str, float]], wordlist: List[str],
                     rnd: Optional[random.Random] = None):
    if rnd is None:
        rnd = random.Random()
    if not pattern_probs:
        return ''.join(rnd.choice(CHARSET) for _ in range(DEFAULT_LENGTH))
    r = rnd.random()
    cum = 0.0
    chosen = pattern_probs[-1][0]
    for pat, p in pattern_probs:
        cum += p
        if r <= cum:
            chosen = pat
            break
    tokens = []
    for tok_type in chosen.split():
        if tok_type == 'W':
            w = rnd.choice(wordlist) if wordlist else ''.join(rnd.choice(CHARSET) for _ in range(3))
            tokens.append(''.join(ch for ch in w if ch.isalpha())[:3])
        else:
            k = rnd.choice([1, 2, 2, 3])
            tokens.append(''.join(rnd.choice('0123456789') for _ in range(k)))
    cand = ''.join(tokens)
    if len(cand) < DEFAULT_LENGTH:
        cand = cand + ('0' * (DEFAULT_LENGTH - len(cand)))
    else:
        cand = cand[:DEFAULT_LENGTH]
    return cand


def get_profile_weights(profile: str):
    if profile == 'conservative':
        return {'pw': 1.5, 'pcfg': 2.0, 'markov': 1.2, 'length_pref': 0.1, 'digit_penalty': -2.0, 'mangling_penalty': -1.0}
    if profile == 'aggressive':
        return {'pw': 0.8, 'pcfg': 1.0, 'markov': 1.8, 'length_pref': 0.2, 'digit_penalty': -0.5, 'mangling_penalty': -0.2}
    return {'pw': 1.0, 'pcfg': 1.5, 'markov': 1.0, 'length_pref': 0.2, 'digit_penalty': -1.0, 'mangling_penalty': -0.5}


def compute_score(candidate: str,
                  word_freq: Counter,
                  pattern_probs: List[Tuple[str, float]],
                  markov_model,
                  alpha_weights: Optional[dict] = None):
    if alpha_weights is None:
        alpha_weights = get_profile_weights('balanced')
    score = 0.0
    if candidate in word_freq:
        score += alpha_weights['pw'] * math.log(1 + word_freq[candidate])
    else:
        for w, cnt in word_freq.most_common(200):
            if w and w in candidate:
                score += alpha_weights['pw'] * math.log(1 + cnt) * 0.5
                break
    pat, _ = token_pattern_from_candidate(candidate)
    pcfg_prob = 1e-9
    for p, pr in pattern_probs:
        if p == pat:
            pcfg_prob = max(pr, 1e-9)
            break
    score += alpha_weights['pcfg'] * math.log(pcfg_prob)
    markov_logp = 0.0
    order = 2
    token = '^' + candidate + '$'
    for i in range(len(token) - (order - 1)):
        hist = token[i:i + order - 1]
        nxt = token[i + order - 1]
        items = markov_model.get(hist)
        if items:
            prev = 0.0
            prob_n = 0.0
            for cum, ch in items:
                prob = cum - prev
                if ch == nxt:
                    prob_n = prob
                    break
                prev = cum
            if prob_n <= 0:
                prob_n = 1e-6
            markov_logp += math.log(prob_n)
        else:
            markov_logp += math.log(1.0 / 36)
    score += alpha_weights['markov'] * markov_logp
    score += alpha_weights.get('length_pref', 0.0) * math.log(1 + len(candidate))
    num_ratio = sum(1 for c in candidate if c.isdigit()) / len(candidate)
    score += alpha_weights.get('digit_penalty', 0.0) * num_ratio
    if candidate[-2:].isdigit():
        score += alpha_weights.get('mangling_penalty', 0.0)
    return score


def producer_priority(queue: mp.Queue, stop_flag: Any, args,
                      wordlist, word_freq, pattern_probs, markov_model, alpha_weights):
    rnd = random.Random(args.seed or 1234)
    max_candidates = args.max_candidates
    generated = 0
    heap: List[Tuple[float, str]] = []
    topk_buffer = args.topk_buffer or 2000
    flush_batch_size = args.batch_size or 512
    last_flush_time = time.time()
    dump_path = args.dump_candidates

    def push_candidate(cand: str):
        nonlocal heap
        if stop_flag.value:
            return
        score = compute_score(cand, word_freq, pattern_probs, markov_model, alpha_weights)
        if len(heap) < topk_buffer:
            heapq.heappush(heap, (score, cand))
        else:
            if score > heap[0][0]:
                heapq.heapreplace(heap, (score, cand))

    def flush_top(n: int):
        nonlocal heap, generated
        if not heap:
            return 0
        top_n = heapq.nlargest(n, heap, key=lambda x: x[0])
        remaining = set((item[1] for item in top_n))
        heap = [(s, c) for (s, c) in heap if c not in remaining]
        heapq.heapify(heap)
        batch = [c for (_, c) in sorted(top_n, key=lambda x: -x[0])]
        try:
            queue.put(batch, timeout=5)
        except Exception:
            pass
        if dump_path:
            try:
                with open(dump_path, 'a', encoding='utf-8') as fo:
                    for c in batch:
                        fo.write(c + '\n')
            except Exception:
                pass
        generated += len(batch)
        return len(batch)

    def gen_tier_a():
        for w in (wordlist[:200000] if wordlist else []):
            if stop_flag.value:
                break
            yield (w[:DEFAULT_LENGTH].ljust(DEFAULT_LENGTH, '0'))

    def gen_tier_b():
        for w in (wordlist[:50000] if wordlist else []):
            if stop_flag.value:
                break
            for v in mangling_variants(w):
                yield v

    def gen_tier_c():
        if pattern_probs and wordlist:
            while not stop_flag.value:
                yield sample_from_pcfg(pattern_probs, wordlist, rnd)

    def gen_tier_d():
        if markov_model:
            while not stop_flag.value:
                yield sample_markov(markov_model, DEFAULT_LENGTH, 2, rnd)

    gens = [gen_tier_a(), gen_tier_b(), gen_tier_c(), gen_tier_d()]
    current_gen_idx = 0
    try:
        while generated < max_candidates and current_gen_idx < len(gens) and not stop_flag.value:
            try:
                cand = next(gens[current_gen_idx])
            except StopIteration:
                current_gen_idx += 1
                continue
            push_candidate(cand)
            if len(heap) >= topk_buffer:
                flush_top(flush_batch_size)
            if time.time() - last_flush_time >= 0.5:
                flush_top(min(flush_batch_size, max(64, len(heap) // 4)))
                last_flush_time = time.time()
        while generated < max_candidates and heap and not stop_flag.value:
            flush_top(min(flush_batch_size, len(heap)))
        while generated < max_candidates and not stop_flag.value:
            batch = []
            for _ in range(min(flush_batch_size, max_candidates - generated)):
                batch.append(''.join(rnd.choice(CHARSET) for _ in range(DEFAULT_LENGTH)))
            try:
                queue.put(batch, timeout=5)
            except Exception:
                pass
            if dump_path:
                try:
                    with open(dump_path, 'a', encoding='utf-8') as fo:
                        for c in batch:
                            fo.write(c + '\n')
                except Exception:
                    pass
            generated += len(batch)
            time.sleep(0.01)
    finally:
        try:
            queue.put(None, timeout=1)
        except Exception:
            pass
        return


def worker_proc(worker_id: int, queue: mp.Queue, stop_flag: Any,
                stats: Any, args, wordlist: List[str]):
    local_count = 0
    target = args.target_hash.lower() if args.target_hash else None
    mode = args.mode
    batch_timeout = 2.0
    last_report = time.time()
    while True:
        if stop_flag.value:
            break
        try:
            batch = queue.get(timeout=batch_timeout)
        except Exception:
            continue
        if batch is None:
            try:
                queue.put(None, timeout=1)
            except Exception:
                pass
            break
        for cand in batch:
            local_count += 1

            # --- 보너스: 워드리스트 포함시 중단 (옵션) ---
            if args.stop_on_dict_match and wordlist:
                # 간단 최적화: 길이 짧은 워드부터 확인하면 빠를 수 있음
                # 여기선 단순 순회: 필요시 wordlist를 짧게 잘라서 검사하거나 해시 기반 검사를 도입해도 됨
                for w in wordlist:
                    if not w:
                        continue
                    if w in cand:
                        with stop_flag.get_lock():
                            stop_flag.value = 1
                        stats['found'] = cand
                        stats['found_by'] = worker_id
                        stats['found_reason'] = f'dict_match:{w}'
                        stats['checked'] = stats.get('checked', 0) + local_count
                        # 문제1: password.txt에 기록
                        try:
                            with open('password.txt', 'w', encoding='utf-8') as pf:
                                pf.write(cand + '\n')
                        except Exception:
                            pass
                        return

            # --- 기존: sha256 비교 (simulate 모드) ---
            if mode == 'simulate' and target:
                if sha256_hex(cand) == target:
                    with stop_flag.get_lock():
                        stop_flag.value = 1
                    stats['found'] = cand
                    stats['found_by'] = worker_id
                    stats['checked'] = stats.get('checked', 0) + local_count
                    # 문제1: 성공하면 password.txt로 저장
                    try:
                        with open('password.txt', 'w', encoding='utf-8') as pf:
                            pf.write(cand + '\n')
                    except Exception:
                        pass
                    return

        now = time.time()
        if now - last_report >= 1.0:
            stats['checked'] = stats.get('checked', 0) + local_count
            stats[f'worker_{worker_id}'] = stats.get(f'worker_{worker_id}', 0) + local_count
            local_count = 0
            last_report = now
    stats['checked'] = stats.get('checked', 0) + local_count


def print_pattern_probs(pattern_probs: List[Tuple[str, float]], top_n: int = 20):
    print('\n[Top patterns]')
    total = sum(p for _, p in pattern_probs) or 1.0
    for i, (pat, prob) in enumerate(pattern_probs[:top_n], 1):
        bar_len = int((prob / total) * 50)
        bar = '#' * bar_len
        print(f'{i:2d}. {pat:10s} | {prob:.6f} | {bar}')
    if not pattern_probs:
        print(' (no pattern data)')


def orchestrate(args):
    mp.set_start_method('spawn', force=True)
    manager = mp.Manager()
    queue = manager.Queue(maxsize=args.queue_maxsize or 4096)
    stop_flag = manager.Value('i', 0)
    stats = manager.dict()
    stats['checked'] = 0
    stats['start_time'] = time.time()
    stats['found'] = None

    wordlist = load_wordlist(args.wordlist, max_words=args.wordlist_max) if args.wordlist else []
    word_freq = build_freq_map(wordlist)
    pattern_probs = train_pcfg_from_wordlist(wordlist, max_patterns=args.pcfg_max_patterns) if wordlist else []
    markov_model = train_markov(wordlist, order=2) if wordlist else {}

    if args.show_patterns:
        print_pattern_probs(pattern_probs, top_n=args.show_patterns_top or 20)

    alpha_weights = get_profile_weights(args.profile or 'balanced')
    if args.pw_weight is not None:
        alpha_weights['pw'] = args.pw_weight
    if args.pcfg_weight is not None:
        alpha_weights['pcfg'] = args.pcfg_weight
    if args.markov_weight is not None:
        alpha_weights['markov'] = args.markov_weight
    if args.digit_penalty is not None:
        alpha_weights['digit_penalty'] = args.digit_penalty
    if args.mangling_penalty is not None:
        alpha_weights['mangling_penalty'] = args.mangling_penalty

    prod = mp.Process(
        target=producer_priority,
        args=(queue, stop_flag, args, wordlist, word_freq, pattern_probs, markov_model, alpha_weights),
        name='producer'
    )
    prod.start()

    workers = []
    for wid in range(args.workers):
        p = mp.Process(
            target=worker_proc,
            args=(wid, queue, stop_flag, stats, args, wordlist),
            name=f'worker-{wid}'
        )
        p.start()
        workers.append(p)

    start = time.time()
    try:
        while True:
            time.sleep(1.0)
            elapsed = time.time() - start
            checked = stats.get('checked', 0)
            rate = checked / elapsed if elapsed > 0 else 0.0
            sys.stdout.write(f'\rElapsed: {int(elapsed)}s | checked: {checked:,} | rate: {rate:,.0f} ops/s')
            sys.stdout.flush()
            if stop_flag.value:
                print('\n[+] stopped: found signal set')
                break
            if args.time_limit and elapsed >= args.time_limit:
                print('\n[-] time limit reached]')
                break
            if not prod.is_alive() and queue.empty():
                alive_workers = any(p.is_alive() for p in workers)
                if not alive_workers:
                    print('\n[*] all done')
                    break
    except KeyboardInterrupt:
        print('\n[!] KeyboardInterrupt: stopping')

    stop_flag.value = 1
    prod.join(timeout=2.0)
    for p in workers:
        p.join(timeout=2.0)
    stats['end_time'] = time.time()
    return dict(stats)


def parse_args():
    p = argparse.ArgumentParser(description='Advanced safe pipeline v2 (priority + pcfg + dump + profiles)')
    p.add_argument('--workers', type=int, default=min(8, mp.cpu_count()), help='worker count')
    p.add_argument('--wordlist', type=str, default=None, help='path to wordlist')
    p.add_argument('--wordlist-max', type=int, default=200000, help='max words to load')
    p.add_argument('--mode', choices=['simulate', 'noop'], default='noop', help='simulate compares sha256 to target; noop just counts')
    p.add_argument('--target-hash', type=str, default=None, help='hex sha256 for simulate mode')
    p.add_argument('--bench', action='store_true', help='run benchmark and exit')
    p.add_argument('--bench-duration', type=float, default=5.0)
    p.add_argument('--time-limit', type=int, default=300, help='seconds')
    p.add_argument('--max-candidates', type=int, default=200_000_000)
    p.add_argument('--seed', type=int, default=1234)
    p.add_argument('--queue-maxsize', type=int, default=4096)
    p.add_argument('--topk-buffer', type=int, default=2000)
    p.add_argument('--batch-size', type=int, default=512)
    p.add_argument('--pcfg-max-patterns', type=int, default=200)
    p.add_argument('--profile', choices=['conservative', 'balanced', 'aggressive'], default='balanced')
    p.add_argument('--pw-weight', type=float, default=None)
    p.add_argument('--pcfg-weight', type=float, default=None)
    p.add_argument('--markov-weight', type=float, default=None)
    p.add_argument('--digit-penalty', type=float, default=None)
    p.add_argument('--mangling-penalty', type=float, default=None)
    p.add_argument('--dump-candidates', type=str, default=None, help='path to append generated candidates (producer writes)')
    p.add_argument('--show-patterns', action='store_true', help='print top patterns (visual) at start')
    p.add_argument('--show-patterns-top', type=int, default=20)

    # 추가 옵션: interactive position & stop-on-dict-match
    p.add_argument('--interactive-position', action='store_true',
                   help='찾았을 때 사용자에게 "몇 번째 자리에서 식별 가능한가?"를 물어보고 result.txt에 저장')
    p.add_argument('--stop-on-dict-match', action='store_true',
                   help='생성된 후보(cand)에 워드리스트의 단어가 포함되면 즉시 중단')

    return p.parse_args()


def main():
    args = parse_args()

    if args.bench:
        res = run_benchmark(workers=args.workers, duration=args.bench_duration)
        print('--- benchmark ---')
        for i, c in enumerate(res['counts']):
            print(f' - worker {i}: {c:,} ops')
        print(f"total: {res['total']:,} in {res['elapsed']:.3f}s -> {res['ops_per_sec']:,} ops/s")
        print(f"keyspace 36^{DEFAULT_LENGTH}: {res['keyspace']:,}")
        print(f"estimated full-search: {res['est_seconds']:.0f}s (~{res['est_seconds']/3600:.2f}h)")
        return

    if args.mode == 'simulate' and not args.target_hash:
        print('[!] simulate requires --target-hash')
        return

    print('[*] starting advanced orchestrator v2')
    stats = orchestrate(args)

    start = stats.get('start_time', time.time())
    end = stats.get('end_time', time.time())
    checked = stats.get('checked', 0)
    elapsed = end - start
    found = stats.get('found')

    print('\n--- summary ---')
    rate = (checked / elapsed) if elapsed > 0 else 0.0
    print(f'elapsed: {elapsed:.2f}s | checked: {checked:,} | rate: {rate:,.0f} ops/s')

    summary = {
        'elapsed_seconds': float(elapsed),
        'checked': int(checked),
        'ops_per_sec': float(rate),
        'found': found,
        'found_by': stats.get('found_by'),
        'timestamp_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }
    try:
        atomic_write_json('result_summary.json', summary)
        print('[*] summary saved -> result_summary.json')
    except Exception as e:
        print(f'[!] failed to write summary: {e}')

    if found:
        print(f'[+] FOUND candidate: {found}')
    else:
        print('[-] Not found in generated set.')

    # --- 추가: result.txt 생성 및 interactive position 처리 (문제2) ---
    payload = {
        'found_candidate': found,
        'found_by': stats.get('found_by'),
        'found_reason': stats.get('found_reason'),
        'checked': int(checked),
        'elapsed_seconds': float(elapsed),
        'timestamp_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }

    if args.interactive_position and found:
        try:
            user_in = input('몇 번째 자리에서 식별 가능한가요? (숫자 입력 또는 빈칸): ').strip()
            if user_in:
                payload['identified_position'] = int(user_in)
        except Exception:
            pass

    try:
        atomic_write_json('result.txt', payload)
        print('[*] result saved -> result.txt')
    except Exception as e:
        print(f'[!] failed to write result.txt: {e}')


if __name__ == '__main__':
    main()
