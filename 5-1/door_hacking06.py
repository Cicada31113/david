import itertools
import string
import time
import zipfile
import multiprocessing as mp
import os
import subprocess
import sys

# --- 상수 정의 ---
ZIP_FILENAME = 'emergency_storage_key.zip'
TARGET_FILE_IN_ZIP = 'password.txt'  # ZIP 파일 안의 암호화된 파일 (문제 요건)
ZIP_PASSWORD_FILENAME = 'password2.txt'  # ZIP을 푼 6자리 암호를 저장할 파일
CAESAR_CIPHER_FILENAME = 'password3.txt'  # 해독할 카이사르 암호문 원본을 저장할 파일
RESULT_FILENAME = 'result.txt'  # 최종 해독 결과를 저장할 파일
CHARSET = string.ascii_lowercase + string.digits
PW_LENGTH = 6
KEYSPACE = len(CHARSET) ** PW_LENGTH

# 카이사르 암호 해독 보너스 요건을 위한 간단한 사전
COMMON_WORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'it',
    'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'password',
    'secret', 'key', 'code', 'unlock', 'access', 'admin'
}
HIGH_PROB_CANDIDATES_COUNT = 500000 # 고확률 후보군 개수 (조정 가능)

def run_hashcat():
    """
    시스템에 hashcat이 설치된 경우 GPU 가속을 시도합니다.
    -m 17210은 ZIP (PKWARE) 모드입니다.
    """
    try:
        # hashcat 존재 여부 확인
        subprocess.run(['hashcat', '--version'], capture_output=True, check=True, text=True)
        print('[INFO] Hashcat detected. Attempting GPU-accelerated cracking...')
    except (FileNotFoundError, subprocess.CalledProcessError):
        print('[INFO] Hashcat not found. Falling back to CPU brute-force.')
        return None

    # hashcat은 zip2john으로 추출한 해시가 필요합니다.
    # 여기서는 편의상 hashcat의 내장 ZIP 모드를 직접 시도합니다.
    # 실제로는 zip2john을 먼저 실행하는 것이 더 안정적입니다.
    command = [
        'hashcat',
        '-m', '17210',  # ZIP (PKWARE)
        '-a', '3',      # Brute-force (mask)
        ZIP_FILENAME,
        '--increment',
        f'--increment-min={PW_LENGTH}',
        f'--increment-max={PW_LENGTH}',
        '-1', string.ascii_lowercase + string.digits,
        '?1?1?1?1?1?1',
        '--potfile-disable',  # potfile 사용 안함
        '--outfile-format=2',  # 암호만 출력
        '--quiet'
    ]
    try:
        # hashcat 실행 (타임아웃을 길게 설정하거나, 사용자가 중단할 때까지 실행)
        result = subprocess.run(command, capture_output=True, text=True, timeout=1800)  # 30분 타임아웃
        if result.stdout:
            password = result.stdout.strip().splitlines()[-1]
            print(f'\n[INFO] Hashcat found password: {password}')
            return password
    except subprocess.TimeoutExpired:
        print('\n[INFO] Hashcat timed out. No password found with GPU.')
    except Exception as e:
        print(f'\n[ERROR] An error occurred with hashcat: {e}')
    return None


def generate_high_probability_candidates():
    """
    엔트로피가 낮고 사용 빈도가 높은 고확률 암호 후보군을 생성합니다.
    (반복, 순차, 흔한 패턴 등)
    """
    candidates = set()

    # 1. 반복 패턴 (e.g., 'aaaaaa', '111111')
    for char in CHARSET:
        candidates.add(char * PW_LENGTH)

    # 2. 순차 패턴 (e.g., 'abcdef', '123456')
    for i in range(len(CHARSET) - PW_LENGTH + 1):
        candidates.add(CHARSET[i:i + PW_LENGTH])
        # 역방향 순차 패턴
        rev_seq = CHARSET[i:i + PW_LENGTH][::-1]
        candidates.add(rev_seq)

    # 3. 흔한 단어 기반 패턴 (패딩 추가)
    common_base = ['admin', 'password', 'secret', 'qwerty', '123456', '123', 'abc']
    for word in common_base:
        if len(word) <= PW_LENGTH:
            # 숫자, 'a', '0' 등으로 패딩
            padding_chars = ['1', 'a', '0']
            for pad_char in padding_chars:
                padded = (word + pad_char * PW_LENGTH)[:PW_LENGTH]
                candidates.add(padded)

    print(f"[INFO] 생성된 고확률 후보군: {len(candidates):,}개")
    return list(candidates)


def find_zip_entry_password_worker(task_queue, found_event, found_queue, progress_queue, worker_id):
    """
    워커 프로세스: 할당된 범위의 비밀번호를 시도하여 ZIP 파일 안의 특정 파일을 읽습니다.
    """
    with zipfile.ZipFile(ZIP_FILENAME, 'r') as zf:
        while not found_event.is_set():
            try:
                # 작업 큐에서 암호 목록(배치)을 가져옴
                passwords = task_queue.get(timeout=0.1)
            except mp.queues.Empty:
                break # 큐가 비었으면 종료

            for password in passwords:
                if found_event.is_set():
                    return

                try:
                    content = zf.read(TARGET_FILE_IN_ZIP, pwd=password.encode('utf-8'))
                    if not found_event.is_set():
                        found_event.set()
                        found_queue.put((password, content))
                    return
                except (RuntimeError, zipfile.BadZipFile):
                    continue
            progress_queue.put(len(passwords))


def unlock_zip():
    """
    (문제 1) ZIP 파일 암호를 찾아 해제합니다. GPU(hashcat)를 우선 시도하고, 실패 시 CPU 병렬 처리를 수행합니다.
    """
    if not os.path.exists(ZIP_FILENAME):
        print(f'[ERROR] {ZIP_FILENAME} not found. Please place it in the same directory.')
        return False

    start_time = time.time()
    print(f"[INFO] Starting password search for '{TARGET_FILE_IN_ZIP}' inside '{ZIP_FILENAME}'...")

    # 1. GPU 가속 시도
    password = run_hashcat()
    if password:
        try:
            with zipfile.ZipFile(ZIP_FILENAME, 'r') as zf:
                content = zf.read(TARGET_FILE_IN_ZIP, pwd=password.encode('utf-8'))
            found_result = (password, content)
        except Exception as e:
            print(f'[ERROR] Hashcat found a password, but failed to extract file: {e}')
            found_result = None  # CPU로 재시도
    else:
        found_result = None

    # 2. GPU 실패/미설치 시 CPU 병렬 처리
    if not found_result:
        print('[INFO] Starting entropy-based CPU parallel attack...')
        num_workers = max(1, os.cpu_count())

        found_event = mp.Event()
        found_queue = mp.Queue()
        progress_queue = mp.Queue()
        task_queue = mp.Queue()

        # --- 지능적인 작업 분배 ---
        # 1. 특공조(Worker 0)를 위한 고확률 후보군 생성
        high_prob_candidates = generate_high_probability_candidates()
        task_queue.put(high_prob_candidates)
        
        # 2. 나머지 일반 병력을 위한 전체 키스페이스 분할
        # 고확률 후보군을 제외한 나머지 공간을 탐색
        brute_force_generator = (p for p in (''.join(p) for p in itertools.product(CHARSET, repeat=PW_LENGTH)) if p not in high_prob_candidates)
        
        # 작업을 10만개 단위의 배치로 나누어 큐에 추가
        batch_size = 100000
        while True:
            batch = list(itertools.islice(brute_force_generator, batch_size))
            if not batch:
                break
            task_queue.put(batch)

        processes = []
        for i in range(num_workers):
            p = mp.Process(target=find_zip_entry_password_worker, args=(task_queue, found_event, found_queue, progress_queue, i))
            processes.append(p)
            p.start()
            print(f"[INFO] Worker {i} started...")

        total_attempts = 0
        try:
            while not found_event.is_set() and any(p.is_alive() for p in processes):
                try:
                    total_attempts += progress_queue.get(timeout=1)
                    elapsed = time.time() - start_time
                    rate = total_attempts / elapsed if elapsed > 0 else 0
                    sys.stdout.write(f'\r[CPU] Attempts: {total_attempts:,} ({total_attempts/KEYSPACE:.2%}) | Rate: {rate:,.0f} p/s | Elapsed: {elapsed:.2f}s')
                    sys.stdout.flush()
                except mp.queues.Empty:
                    continue
        except KeyboardInterrupt:
            print('\n[INFO] User interrupted. Terminating workers...')
            found_event.set()

        if found_event.is_set() and not found_queue.empty():
            found_result = found_queue.get()

        for p in processes:
            p.terminate()
            p.join()

    elapsed_time = time.time() - start_time
    print()  # 줄바꿈

    if found_result:
        zip_password, file_content = found_result
        print('\n' + '=' * 50)
        print(f"  Success! Password for '{TARGET_FILE_IN_ZIP}' found: {zip_password}")
        print(f'  Elapsed time: {elapsed_time:.2f} seconds')
        print('=' * 50)
        try:
            with open(ZIP_PASSWORD_FILENAME, 'w', encoding='utf-8') as f:
                f.write(zip_password)
            print(f"[INFO] ZIP entry password saved to '{ZIP_PASSWORD_FILENAME}'")

            with open(CAESAR_CIPHER_FILENAME, 'w', encoding='utf-8') as f:
                f.write(file_content.decode('utf-8'))
            print(f"[INFO] Content to be decrypted saved to '{CAESAR_CIPHER_FILENAME}'.")
            return True
        except IOError as e:
            print(f'[ERROR] Error writing files: {e}')
            return False
    else:
        print('\n[FAIL] Password not found after checking all combinations.')
        return False


def caesar_cipher_decode(target_text):
    """
    (문제 2) 주어진 텍스트(카이사르 암호문)를 해독하고 결과를 result.txt에 저장합니다.
    """
    print('\n' + '=' * 50)
    print('  Starting Caesar cipher decoding...')
    print(f'  Original text: {target_text}')
    print('=' * 50)

    decrypted_results = []
    plausible_shifts = []
    # 알파벳 수(26)만큼 반복하여 모든 shift 경우의 수를 테스트합니다.
    for shift in range(26):
        result = ''
        for char in target_text:
            # islower(), isupper()로 대소문자 구분
            if char.islower():
                shifted_code = ord('a') + (ord(char) - ord('a') - shift) % 26
                result += chr(shifted_code)
            elif char.isupper():
                shifted_code = ord('A') + (ord(char) - ord('A') - shift) % 26
                result += chr(shifted_code)
            else: # 알파벳이 아니면 그대로 유지
                result += char
        decrypted_results.append(result)
        # 보너스: 해독된 문장에 일반적인 영어 단어가 포함되어 있는지 확인
        # 문장을 소문자로 바꾸고 단어로 분리하여 사전에 있는지 검사합니다.
        found_words = {word for word in COMMON_WORDS if word in result.lower().split()}
        
        # 자리수(shift+1)에 따라 해독된 결과를 출력합니다.
        if found_words:
            plausible_shifts.append((shift + 1, result, found_words))
            print(f'Shift #{shift + 1:02d}: {result}  <-- Plausible, contains: {", ".join(found_words)}')
        else:
            print(f'Shift #{shift + 1:02d}: {result}')

    if plausible_shifts:
        print('\n[INFO] Automatically detected plausible results. You may choose from these.')

    # 사용자가 눈으로 식별하고 번호를 입력하면 결과를 저장합니다.
    while True:
        try:
            user_input = input(f'\nEnter the correct shift number to save the result (1-26): ')
            correct_shift = int(user_input)

            if 1 <= correct_shift <= 26:
                # 사용자가 입력한 번호는 1-26, 리스트 인덱스는 0-25 이므로 -1을 해줍니다.
                final_text = decrypted_results[correct_shift - 1]

                try:
                    # 최종 암호를 result.txt로 저장합니다.
                    with open(RESULT_FILENAME, 'w', encoding='utf-8') as f:
                        f.write(final_text)
                    print(f"\n[SUCCESS] Decoded text saved to '{RESULT_FILENAME}'")
                    print(f'  Final result: {final_text}')
                    break
                except IOError as e:
                    print(f'[ERROR] Error writing result to file: {e}')
                    break
            else:
                print('[ERROR] Invalid number. Please enter a number between 1 and 26.')
        except ValueError:
            print('[ERROR] Invalid input. Please enter a number.')


def main():
    """전체 과제 실행을 관리하는 메인 함수"""
    # --- 문제 1: ZIP 파일 안의 파일 암호 풀기 ---
    # 카이사르 암호문이 담긴 파일이 없으면 암호 풀기를 시도합니다.
    if not os.path.exists(CAESAR_CIPHER_FILENAME):
        if not unlock_zip():
            print('\n[FATAL] Failed to unlock the ZIP file entry. Exiting.')
            return
    else:
        print(f"[INFO] '{CAESAR_CIPHER_FILENAME}' already exists. Skipping ZIP entry unlocking.")

    # --- 문제 2: 카이사르 암호 해독 ---
    try:
        # 문제 요건: password.txt(여기서는 caesar_cipher_source.txt) 파일을 읽어옵니다.
        with open(CAESAR_CIPHER_FILENAME, 'r', encoding='utf-8') as f:
            encrypted_password = f.read().strip()

        if encrypted_password:
            caesar_cipher_decode(encrypted_password)
        else:
            print(f'[ERROR] {CAESAR_CIPHER_FILENAME} is empty.')

    except FileNotFoundError:
        print(f"[ERROR] '{CAESAR_CIPHER_FILENAME}' not found.")
        print('Please run the unlock_zip() part first or create the file manually.')
    except Exception as e:
        print(f'[ERROR] An error occurred while reading the password file: {e}')


if __name__ == '__main__':
    # Windows에서 multiprocessing을 안정적으로 사용하기 위해 필요
    mp.freeze_support()
    main()