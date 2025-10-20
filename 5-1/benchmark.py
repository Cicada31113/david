# bench.py (실행용)
# 목적: 문자열 생성 + SHA256 해싱 처리량(ops/sec) 측정
# 주의: 암호해제나 ZIP 접근을 시도하지 않음. 순수 연산 벤치마크용.

import multiprocessing as mp
import time
import hashlib
import random

def worker(worker_id: int, duration: float, charset: str, length: int, return_dict):
    rnd = random.Random(worker_id + int(time.time()))
    end_time = time.time() + duration
    cnt = 0
    _choice = rnd.choice
    _encode = str.encode
    _sha256 = hashlib.sha256
    while time.time() < end_time:
        s = ''.join(_choice(charset) for _ in range(length))
        _sha256(_encode(s)).digest()
        cnt += 1
    return_dict[worker_id] = cnt

def run_benchmark(workers: int = None, duration: float = 5.0, length: int = 6):
    charset = '0123456789abcdefghijklmnopqrstuvwxyz'
    if workers is None:
        try:
            workers = min(8, mp.cpu_count())
        except NotImplementedError:
            workers = 8
    manager = mp.Manager()
    return_dict = manager.dict()
    procs = []
    start = time.time()
    for wid in range(workers):
        p = mp.Process(target=worker, args=(wid, duration, charset, length, return_dict))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
    elapsed = time.time() - start
    counts = [return_dict.get(wid, 0) for wid in range(workers)]
    total = sum(counts)
    ops_per_sec = total / elapsed if elapsed > 0 else 0.0

    keyspace = 36 ** length
    est_seconds = keyspace / ops_per_sec if ops_per_sec > 0 else float('inf')
    est_hours = est_seconds / 3600
    est_days = est_hours / 24

    print(f'Workers used: {workers}')
    for wid, cnt in enumerate(counts):
        print(f' - Worker {wid}: {cnt:,} ops')
    print(f'Total ops: {total:,}')
    print(f'Elapsed time: {elapsed:.3f} sec')
    print(f'Aggregate throughput: {ops_per_sec:,.0f} ops/sec')
    print()
    print('Keyspace estimate:')
    print(f' - Keyspace (36^{length}): {keyspace:,} candidates')
    if ops_per_sec > 0:
        print(f' - Estimated full-search time: {est_seconds:,.0f} sec (~{est_hours:,.2f} hours / {est_days:,.2f} days)')
    else:
        print(' - Ops/sec measured as 0, cannot estimate full-search time.')

if __name__ == "__main__":
    run_benchmark(workers=None, duration=5.0, length=6)
