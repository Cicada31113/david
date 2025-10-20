from __future__ import annotations
"""
door_hacking_fixed.py
오리지널 door_hacking.py의 Pylance 타입 경고("Variable not allowed in type expression") 문제 해결판.
- Python 3.x (권장 3.8+)
- 같은 디렉토리에 emergency_storage_key.zip 두고 실행
- 사용: python door_hacking_fixed.py [zip_path]
"""

import itertools
import time
import sys
from multiprocessing import Process, Event, Value, Lock, cpu_count, current_process
from zipfile import ZipFile, BadZipFile

# 상수
CHARSET = '0123456789abcdefghijklmnopqrstuvwxyz'  # 숫자 + 소문자
PW_LENGTH = 6
STATUS_INTERVAL = 10000  # 워커 단위 상태 출력 빈도 (시도 횟수 단위)


def try_passwords_worker(zip_path, prefixes, found_event, found_password_flag, attempt_counter, counter_lock):
    """
    워커 프로세스:
    - prefixes: 워커가 책임질 접두사 리스트 (예: ['a','b','0',...])
    - found_event: multiprocessing.Event (다른 프로세스에 발견 통지)
    - found_password_flag: multiprocessing.Value (플래그용)
    - attempt_counter: multiprocessing.Value (대략적 시도 횟수 공유)
    - counter_lock: multiprocessing.Lock
    """
    proc_name = current_process().name
    try:
        zf = ZipFile(zip_path, 'r')
    except BadZipFile:
        print(f'[{proc_name}] Bad zip file: {zip_path}')
        return

    namelist = zf.namelist()
    if not namelist:
        print(f'[{proc_name}] zip is empty.')
        return

    # 우선 'password.txt' 시도, 없으면 첫 파일
    target_file = 'password.txt' if 'password.txt' in namelist else namelist[0]

    local_count = 0
    start = time.time()

    # 각 prefix에 대해 tail 을 brute-force
    for prefix in prefixes:
        if found_event.is_set():
            break
        tail_len = PW_LENGTH - len(prefix)
        # product 순회: tail_len이 0이면 바로 검사(완전한 prefix)
        if tail_len == 0:
            candidates = (prefix,)
        else:
            candidates = (prefix + ''.join(t) for t in itertools.product(CHARSET, repeat=tail_len))

        for candidate in candidates:
            if found_event.is_set():
                break
            try:
                zf.read(target_file, pwd=candidate.encode('utf-8'))
                # 성공
                with counter_lock:
                    # 실제 패스워드는 파일로 바로 저장 (메인 프로세스가 읽도록)
                    found_password_flag.value = 1
                with open('password.txt', 'w', encoding='utf-8') as f:
                    f.write(candidate)
                with open('result.txt', 'w', encoding='utf-8') as f:
                    f.write(candidate)
                found_event.set()
                elapsed = time.time() - start
                print(f'[{proc_name}] FOUND password="{candidate}" (local tries ~{local_count}) elapsed={elapsed:.2f}s')
                return
            except RuntimeError:
                # 잘못된 비밀번호 경우 zipfile에서 RuntimeError 가 발생할 수 있음
                pass
            except Exception:
                # 읽기 실패 등 기타 예외 무시하고 계속
                pass

            local_count += 1
            # 전체 카운터에 주기적으로 반영 (너무 잦은 업데이트는 성능저하)
            if local_count % 100 == 0:
                with counter_lock:
                    attempt_counter.value += 100

            if local_count % STATUS_INTERVAL == 0:
                with counter_lock:
                    total_attempts = attempt_counter.value
                elapsed = time.time() - start
                print(f'[{proc_name}] tried ~{local_count} this-prefix, total tries ~{total_attempts}, elapsed={elapsed:.2f}s')

    elapsed = time.time() - start
    print(f'[{proc_name}] done, elapsed={elapsed:.2f}s, tried ~{local_count}')


def split_prefixes(n_workers):
    """
    CHARSET의 첫 글자 단위로 균등 배분 (간단한 분배기)
    반환: 워커 수 만큼의 prefix 리스트 묶음
    """
    prefixes = list(CHARSET)
    groups = [[] for _ in range(n_workers)]
    for i, p in enumerate(prefixes):
        groups[i % n_workers].append(p)
    return groups


def unlock_zip(zip_path, n_workers=None):
    """
    메인 함수: 병렬 워커를 띄워 zip 암호를 시도한다.
    """
    if n_workers is None:
        n_workers = min(8, cpu_count())
    else:
        n_workers = max(1, int(n_workers))

    print(f'[main] starting unlock_zip on "{zip_path}" with {n_workers} workers')
    start_time = time.time()

    found_event = Event()
    attempt_counter = Value('Q', 0)  # unsigned long long
    found_password_flag = Value('i', 0)  # 플래그용
    counter_lock = Lock()

    groups = split_prefixes(n_workers)
    procs = []

    # 프로세스 생성 및 시작
    for i in range(n_workers):
        p = Process(
            target=try_passwords_worker,
            name=f'Worker-{i+1}',
            args=(zip_path, groups[i], found_event, found_password_flag, attempt_counter, counter_lock)
        )
        p.daemon = True
        p.start()
        procs.append(p)

    try:
        # 모니터링 루프
        while True:
            if found_event.is_set():
                print('[main] password found, terminating other workers...')
                break
            alive = any(p.is_alive() for p in procs)
            if not alive:
                print('[main] all workers finished without finding password.')
                break
            with counter_lock:
                total = attempt_counter.value
            elapsed = time.time() - start_time
            print(f'[main] total tries ~{total}, elapsed={elapsed:.2f}s')
            time.sleep(2)
    except KeyboardInterrupt:
        print('[main] KeyboardInterrupt received. Terminating workers...')
        found_event.set()
    finally:
        # 종료 처리
        for p in procs:
            if p.is_alive():
                p.terminate()
        for p in procs:
            p.join()

        elapsed_total = time.time() - start_time
        with counter_lock:
            total = attempt_counter.value
        print(f'[main] finished. total tries ~{total}, total_elapsed={elapsed_total:.2f}s')
        if found_event.is_set():
            print('[main] password saved to password.txt and result.txt')
        else:
            print('[main] password not found by this run.')


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        zipfile_path = sys.argv[1]
    else:
        zipfile_path = 'emergency_storage_key.zip'

    try:
        unlock_zip(zipfile_path, n_workers=8)
    except Exception as ex:
        print(f'[main] unexpected error: {ex}')
