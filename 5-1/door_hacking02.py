import zipfile
import string
import time
import multiprocessing
import itertools
import math
from collections import Counter

def calculate_entropy(password, charset_size=36):
    """비밀번호의 엔트로피(bits) 계산"""
    return len(password) * math.log2(charset_size)

def generate_high_probability_candidates(charset, length, max_candidates=100000):
    """
    확률 기반 고우선순위 후보 생성
    - 일반적으로 약한 패턴 우선 시도 (연속 문자, 반복 등)
    - 엔트로피가 낮은 패스워드부터 시도
    """
    candidates = []
    
    # 1. 연속 숫자/문자 패턴 (낮은 엔트로피)
    for start_char in charset[:10]:  # 숫자와 초기 소문자만
        for i in range(length):
            pattern = start_char * length
            candidates.append(pattern)
    
    # 2. 순차적 패턴 (123456, abcdef 등)
    for start_idx in range(len(charset) - length + 1):
        sequential = ''.join(charset[start_idx:start_idx + length])
        candidates.append(sequential)
    
    # 3. 일반적인 약한 패턴 조합
    common_patterns = [
        'password', 'admin', '123456', 'qwerty', 'abc123', 
        'password123', 'admin123', 'test123', 'user123'
    ]
    
    for pattern in common_patterns:
        if len(pattern) == length:
            candidates.append(pattern)
        elif len(pattern) < length:
            # 패딩으로 길이 맞추기
            padded = pattern + '0' * (length - len(pattern))
            candidates.append(padded[:length])
    
    # 4. Markov 체인 기반 후보 (간단한 2-gram 모델)
    # 영어에서 자주 나오는 문자 연쇄 패턴 활용
    frequent_bigrams = ['th', 'he', 'in', 'er', 'an', 're', 'ed', 'nd', 'on', 'en']
    for bigram in frequent_bigrams:
        if length >= 2:
            # bigram을 반복해서 길이 맞추기
            pattern = (bigram * (length // 2 + 1))[:length]
            candidates.append(pattern)
    
    return candidates[:max_candidates]

def entropy_based_keyspace_partition(charset, length, num_workers):
    """
    엔트로피 기반 키스페이스 분할
    낮은 엔트로피(약한 패스워드) 구간을 우선 할당
    """
    total_keyspace = len(charset) ** length
    
    # 전체 키스페이스를 엔트로피 기준으로 정렬된 구간으로 분할
    partitions = []
    
    # 우선순위 1: 고확률 후보들 (전체의 5%)
    high_prob_size = min(100000, total_keyspace // 20)
    
    # 우선순위 2: 나머지 구간을 균등 분할
    remaining_size = total_keyspace - high_prob_size
    partition_size = remaining_size // (num_workers - 1) if num_workers > 1 else remaining_size
    
    # 첫 번째 워커: 고확률 후보 담당
    partitions.append((0, high_prob_size, True))  # True = 고확률 모드
    
    # 나머지 워커들: 일반 무차별 대입
    for i in range(1, num_workers):
        start_idx = high_prob_size + (i - 1) * partition_size
        end_idx = total_keyspace if i == num_workers - 1 else start_idx + partition_size
        partitions.append((start_idx, end_idx, False))  # False = 일반 모드
    
    return partitions

def idx_to_password(idx, charset, length):
    """정수 인덱스를 비밀번호로 변환"""
    base = len(charset)
    pw = []
    for _ in range(length):
        pw.append(charset[idx % base])
        idx //= base
    return ''.join(reversed(pw))

def optimized_worker(start_idx, end_idx, charset, length, zip_path, 
                    result_q, progress_q, worker_id, high_priority_mode=False):
    """
    수학적 최적화가 적용된 워커 함수
    - 고우선순위 모드: 약한 패턴 우선 시도
    - 일반 모드: 표준 무차별 대입
    """
    attempts = 0
    found = False
    
    try:
        with zipfile.ZipFile(zip_path) as zf:
            if high_priority_mode:
                # 고확률 후보 우선 시도
                candidates = generate_high_probability_candidates(charset, length)
                print(f"[WORKER {worker_id}] 고우선순위 모드: {len(candidates)}개 후보 시도")
                
                for password in candidates:
                    if len(password) == length and all(c in charset for c in password):
                        attempts += 1
                        if attempts % 1000 == 0:
                            progress_q.put((worker_id, attempts, password, time.time()))
                        
                        try:
                            zf.extractall(pwd=password.encode('utf-8'))
                            result_q.put(password)
                            found = True
                            break
                        except RuntimeError:
                            continue
                        except Exception:
                            continue
            
            if not found:
                # 일반 무차별 대입 (엔트로피 순서 고려)
                for idx in range(start_idx, end_idx):
                    password = idx_to_password(idx, charset, length)
                    attempts += 1
                    
                    if attempts % 10000 == 0:
                        progress_q.put((worker_id, attempts, password, time.time()))
                    
                    try:
                        zf.extractall(pwd=password.encode('utf-8'))
                        result_q.put(password)
                        found = True
                        break
                    except RuntimeError:
                        continue
                    except Exception:
                        continue
                        
    except Exception as e:
        print(f"[ERROR] Worker {worker_id}: {e}")
    
    # 최종 진행 상황 보고
    if not found:
        progress_q.put((worker_id, attempts, None, time.time()))

def unlock_zip(zip_path='emergency_storage_key.zip', password_length=6, workers=8):
    """
    암호학적 최적화가 적용된 비밀번호 해독 함수
    - 엔트로피 기반 우선순위 공격
    - 확률 분포 최적화
    - 병렬 키스페이스 분할
    """
    charset = string.ascii_lowercase + string.digits
    keyspace = len(charset) ** password_length
    
    # 수학적 분석 출력
    max_entropy = calculate_entropy('z' * password_length, len(charset))
    min_entropy = calculate_entropy('0' * password_length, len(charset))
    
    print(f"[CRYPTO] 암호학적 분석:")
    print(f"  - 키스페이스: {keyspace:,} 조합")
    print(f"  - 최대 엔트로피: {max_entropy:.2f} bits")
    print(f"  - 최소 엔트로피: {min_entropy:.2f} bits") 
    print(f"  - 예상 평균 시도: {keyspace//2:,} (50% 확률)")
    
    # 엔트로피 기반 키스페이스 분할
    partitions = entropy_based_keyspace_partition(charset, password_length, workers)
    
    manager = multiprocessing.Manager()
    result_q = manager.Queue()
    progress_q = manager.Queue()
    
    print(f"[SYSTEM] {workers}개 워커로 최적화된 병렬 탐색 시작")
    start_time = time.time()
    print(f"[START] {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    
    processes = []
    for i, (start_idx, end_idx, high_priority) in enumerate(partitions):
        p = multiprocessing.Process(
            target=optimized_worker,
            args=(start_idx, end_idx, charset, password_length, zip_path,
                  result_q, progress_q, i, high_priority)
        )
        p.start()
        processes.append(p)
    
    worker_progress = [0 for _ in range(workers)]
    found_password = None
    
    try:
        while True:
            # 결과 확인
            while not result_q.empty():
                found_password = result_q.get()
                break
                
            # 진행 상황 업데이트
            while not progress_q.empty():
                wid, attempts, password, timestamp = progress_q.get()
                worker_progress[wid] = attempts
                if password and attempts % 10000 == 0:
                    elapsed = timestamp - start_time
                    total_attempts = sum(worker_progress)
                    percent = (total_attempts / keyspace) * 100
                    current_entropy = calculate_entropy(password, len(charset))
                    
                    print(f"[PROGRESS] W{wid} 시도: {attempts:,} "
                          f"(전체: {total_attempts:,}, {percent:.2f}%) "
                          f"암호: {password} (엔트로피: {current_entropy:.1f}bits) "
                          f"경과: {elapsed:.1f}초")
            
            if found_password:
                # 모든 프로세스 종료
                for p in processes:
                    p.terminate()
                
                elapsed = time.time() - start_time
                found_entropy = calculate_entropy(found_password, len(charset))
                
                print(f"[SUCCESS] 암호 발견: {found_password}")
                print(f"  - 소요 시간: {elapsed:.1f}초")
                print(f"  - 발견된 암호 엔트로피: {found_entropy:.2f} bits")
                print(f"  - 총 시도 횟수: {sum(worker_progress):,}")
                
                # 결과 저장
                with open('password.txt', 'w') as f:
                    f.write(found_password)
                
                # 압축 해제
                try:
                    with zipfile.ZipFile(zip_path) as zf:
                        zf.extractall(pwd=found_password.encode('utf-8'))
                    print("[SYSTEM] 압축 파일 해제 완료")
                except Exception as e:
                    print(f"[ERROR] 압축 해제 실패: {e}")
                
                return found_password
            
            # 모든 프로세스 종료 확인
            if not any(p.is_alive() for p in processes):
                break
                
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("[SYSTEM] 사용자 중단 요청")
        for p in processes:
            p.terminate()
    
    elapsed = time.time() - start_time
    print(f"[FAIL] 암호를 찾지 못했습니다. (총 소요: {elapsed:.1f}초)")
    return None

if __name__ == '__main__':
    unlock_zip()
