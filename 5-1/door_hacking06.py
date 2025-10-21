import itertools
import string
import time
import multiprocessing as mp
import threading
import zipfile
import zlib
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


def generate_hybrid_attack_candidates():
    """
    사전 단어와 변형 규칙을 결합한 하이브리드 공격 후보군을 생성합니다.
    (e.g., password -> p@ssw0rd, admin -> admin123)
    """
    # 외부 파일 의존성 없이, 핵심 단어를 내장
    core_words = [
        'password', 'admin', 'secret', 'user', 'test', 'guest', 'login',
        'master', 'qwerty', '123456', 'hello', 'world', 'key', 'code'
    ]

    candidates = set()

    # 규칙 1: Leet 변환 (e.g., o -> 0, e -> 3)
    leet_map = {'o': '0', 'e': '3', 'l': '1', 'a': '@', 's': '5'}
    mangled_words = set(core_words)
    for word in core_words:
        new_word = word
        for char, replacement in leet_map.items():
            if char in new_word:
                new_word = new_word.replace(char, replacement)
        mangled_words.add(new_word)

    # 규칙 2: 숫자/기호 추가
    suffixes = ['1', '12', '123', '!', '@', '#', '1!', '123!@#']
    for word in mangled_words:
        # 단어 자체 추가
        if len(word) == PW_LENGTH:
            candidates.add(word)
        # 접미사 추가
        for suffix in suffixes:
            combined = word + suffix
            if len(combined) == PW_LENGTH:
                candidates.add(combined)
            # 길이가 짧으면 숫자 '0'으로 패딩
            elif len(combined) < PW_LENGTH:
                candidates.add((combined + '0' * PW_LENGTH)[:PW_LENGTH])

    print(f"[INFO] 생성된 하이브리드 공격 후보군: {len(candidates):,}개")
    return list(candidates)


def generate_probabilistic_hotspots(num_hotspots=5):
    """
    양자 중첩 아이디어에서 착안, 가장 확률이 높은 암호 공간 '핫스팟'을 생성합니다.
    핫스팟은 (마스크, 문자셋) 형태로 정의됩니다. 예: ('pass??', '0123...9')
    """
    hotspots = []
    
    # 핫스팟 1: 'pass' + 2자리 숫자/소문자
    hotspots.append(('pass??', string.digits + string.ascii_lowercase))
    
    # 핫스팟 2: 'admin' + 1자리 숫자/소문자
    hotspots.append(('admin?', string.digits + string.ascii_lowercase))

    # 핫스팟 3: 4자리 숫자 + '00'
    hotspots.append(('????00', string.digits))

    # 핫스팟 4: 'qwerty' 또는 '123456' 같은 순차 패턴
    hotspots.append(('123456', None)) # 고정값
    hotspots.append(('qwerty', None)) # 고정값

    # 핫스팟 5: 반복되는 문자 (e.g., aaaaaa)
    for char in 'abcdefghijklmnopqrstuvwxyz0123456789':
        hotspots.append((char*6, None))

    print(f"[INFO] {len(hotspots)}개의 확률적 핫스팟 생성 완료.")
    return hotspots


def expand_hotspot(mask, charset):
    """핫스팟 마스크를 실제 암호 후보 리스트로 확장합니다."""
    if '?' not in mask:
        return [mask]

    q_indices = [i for i, char in enumerate(mask) if char == '?']
    num_q = len(q_indices)
    
    candidates = []
    for combo in itertools.product(charset, repeat=num_q):
        temp_list = list(mask)
        for i, char in zip(q_indices, combo):
            temp_list[i] = char
        candidates.append("".join(temp_list))
    return candidates


class PkzipLegacy:
    """PKZIP 전통적 암호화(ZipCrypto) 관련 계산 클래스"""
    def __init__(self, password: bytes):
        self.keys = [0x12345678, 0x23456789, 0x34567890]
        for byte in password:
            self.update_keys(byte)

    def update_keys(self, byte: int):
        self.keys[0] = zlib.crc32(bytes([byte]), self.keys[0])
        self.keys[1] = (self.keys[1] + (self.keys[0] & 0xff)) * 0x8088405 + 1
        self.keys[2] = zlib.crc32(bytes([self.keys[1] >> 24]), self.keys[2])

    def decrypt(self, ciphertext: bytes) -> bytes:
        plaintext = bytearray()
        for byte in ciphertext:
            k = self.keys[2] | 2
            temp = byte ^ (((k * (k ^ 1)) >> 8) & 0xff)
            plaintext.append(temp)
            self.update_keys(temp)
        return bytes(plaintext)


def find_zip_entry_password_worker(task_queue, found_event, found_queue, progress_queue, worker_id, zip_header, target_crc):
    """
    워커 프로세스: 초고속 CRC32 비교를 통해 암호 후보를 찾습니다.
    """
    try:
        while not found_event.is_set():
            try:
                passwords = task_queue.get(timeout=0.1)
            except mp.queues.Empty:
                break

            for password in passwords:
                if found_event.is_set():
                    return

                # PkzipLegacy 클래스를 사용하여 암호화 키 초기화
                crypto = PkzipLegacy(password.encode('utf-8'))
                
                # 12바이트 헤더를 복호화 시도
                decrypted_header = crypto.decrypt(zip_header)
                
                # 마지막 바이트가 타겟 CRC와 일치하는지 초고속으로 비교
                if decrypted_header[-1] == (target_crc >> 24):
                    # CRC가 일치할 가능성이 매우 높으므로, 최종 검증
                    try:
                        with zipfile.ZipFile(ZIP_FILENAME) as zf:
                            content = zf.read(TARGET_FILE_IN_ZIP, pwd=password.encode('utf-8'))
                            found_event.set()
                            found_queue.put((password, content))
                        return
                    except (RuntimeError, zipfile.BadZipFile):
                        continue # CRC는 맞았지만 최종 암호가 틀린 희귀 케이스
            
            progress_queue.put(len(passwords))

    except Exception as e:
        print(f"[ERROR] Worker {worker_id} encountered an unexpected error: {e}")


def run_benchmark(duration_sec=2):
    """
    짧은 시간 동안 벤치마크를 실행하여 현재 시스템의 단일 코어 성능을 측정합니다.
    CRC32 비교 방식의 속도를 측정합니다.
    """
    print(f"[INFO] Running a {duration_sec}-second benchmark to estimate performance...")
    attempts = 0
    start_time = time.time()
    password_generator = itertools.product(CHARSET, repeat=PW_LENGTH)
    
    # CRC32 비교를 위한 더미 데이터
    dummy_header = b'\x00' * 12
    dummy_crc_byte = 0

    while time.time() - start_time < duration_sec:
        password = ''.join(next(password_generator))
        crypto = PkzipLegacy(password.encode('utf-8'))
        decrypted_header = crypto.decrypt(dummy_header)
        if decrypted_header[-1] == dummy_crc_byte:
            pass # 실제로는 거의 발생하지 않음
        attempts += 1
    
    rate = attempts / duration_sec
    return rate


def unlock_zip():
    """
    (문제 1) ZIP 파일 암호를 찾아 해제합니다. GPU(hashcat)를 우선 시도하고, 실패 시 CRC32 사전 계산 공격을 수행합니다.
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

    # 2. GPU 실패/미설치 시 CPU 병렬 처리 (CRC32 사전 계산 공격)
    if not found_result:
        # 2-1. ZIP 파일 헤더에서 CRC32와 암호화된 헤더 12바이트 추출
        try:
            with open(ZIP_FILENAME, 'rb') as f:
                zf = zipfile.ZipFile(f)
                target_info = zf.getinfo(TARGET_FILE_IN_ZIP)
                if not target_info.flag_bits & 0x1:
                    print("[ERROR] Target file is not encrypted.")
                    return False
                
                target_crc = target_info.CRC
                f.seek(target_info.header_offset)
                # Local File Header (30 bytes) + filename length
                header_plus_filename_size = 30 + len(target_info.filename)
                f.seek(header_plus_filename_size, 1)
                zip_header = f.read(12) # 암호화된 데이터의 첫 12바이트
                print(f"[INFO] Target CRC32: {target_crc}, Header snippet extracted.")
        except Exception as e:
            print(f"[FATAL] Failed to analyze ZIP file structure: {e}")
            return False

        # 2-2. 벤치마크 실행 및 예상 시간 계산
        single_core_rate = run_benchmark()
        num_workers = max(1, os.cpu_count())
        if single_core_rate > 0:
            estimated_rate = single_core_rate * num_workers * 0.9 # 병렬 처리 오버헤드 감안
            estimated_seconds = KEYSPACE / estimated_rate
            estimated_time_str = time.strftime('%M minutes, %S seconds', time.gmtime(estimated_seconds))
            print(f"[INFO] System benchmark: ~{single_core_rate:,.0f} p/s per core (CRC32 method).")
            print(f"[INFO] With {num_workers} cores, estimated total time for full scan: {estimated_time_str}")
        
        print('[INFO] Starting CRC32 Pre-computation Attack...')

        found_event = mp.Event()
        found_queue = mp.Queue()
        progress_queue = mp.Queue()
        task_queue = mp.Queue()

        # --- 동적 작업 분배를 위한 작업 생성 ---
        # 1. (양자적 접근) 각 핫스팟을 확장하여 공격 후보군 생성 및 큐에 추가
        hotspots = generate_probabilistic_hotspots()
        hotspot_candidates = set()

        def populate_hotspots():
            for mask, charset in hotspots:
                if found_event.is_set(): break
                candidates = expand_hotspot(mask, charset if charset else "")
                task_queue.put(candidates)
                hotspot_candidates.update(candidates)

        hotspot_producer_thread = threading.Thread(target=populate_hotspots)
        hotspot_producer_thread.start()


        # 2. (안전장치) 전체 키스페이스에 대한 무차별 대입 작업을 배치 단위로 생성
        def populate_queue():
            high_prob_set = hotspot_candidates
            password_generator = (''.join(p) for p in itertools.product(CHARSET, repeat=PW_LENGTH) if ''.join(p) not in high_prob_set)
            batch_size = 500000 # 배치 크기를 늘려 오버헤드 감소
            while not found_event.is_set():
                batch = list(itertools.islice(password_generator, batch_size))
                if not batch:
                    break # 모든 암호 생성 완료
                task_queue.put(batch)

        producer_thread = threading.Thread(target=populate_queue)
        producer_thread.start()

        processes = []
        for i in range(num_workers):
            p = mp.Process(target=find_zip_entry_password_worker, args=(task_queue, found_event, found_queue, progress_queue, i, zip_header, target_crc))
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
                    # 진행률은 전체 키스페이스 기준으로 표시 (핫스팟은 보너스)
                    total_keyspace_with_high_prob = KEYSPACE
                    sys.stdout.write(f'\r[CPU] Attempts: {total_attempts:,}/{total_keyspace_with_high_prob:,} ({(total_attempts/total_keyspace_with_high_prob):.2%}) | Rate: {rate:,.0f} p/s | Elapsed: {elapsed:.2f}s')
                    sys.stdout.flush()
                except mp.queues.Empty:
                    continue
        except KeyboardInterrupt:
            print('\n[INFO] User interrupted. Terminating workers...')
            found_event.set()

        if found_event.is_set() and not found_queue.empty():
            found_result = found_queue.get()

        # 작업 생성 스레드 및 워커 프로세스 정리
        hotspot_producer_thread.join()
        producer_thread.join()

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
    best_match = {'score': -1, 'shift': -1, 'text': ''}
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
        words_in_result = result.lower().split()
        found_words = {word for word in COMMON_WORDS if word in words_in_result}
        score = len(found_words)
        
        # 자리수(shift+1)에 따라 해독된 결과를 출력합니다.
        if score > 0:
            print(f'Shift #{shift + 1:02d}: {result}  <-- Plausible, contains: {", ".join(found_words)}')
            if score > best_match['score']:
                best_match = {'score': score, 'shift': shift + 1, 'text': result}
        else:
            print(f'Shift #{shift + 1:02d}: {result}')

    # 가장 가능성 높은 결과를 자동으로 선택하여 저장
    if best_match['score'] > 0:
        print('\n' + '-' * 50)
        print(f"[AUTO-SELECT] Best match found at Shift #{best_match['shift']} with {best_match['score']} common words.")
        final_text = best_match['text']
    else:
        # 그럴듯한 결과를 찾지 못하면 첫 번째 결과(shift 1)를 기본값으로 사용
        print('\n[INFO] No plausible result found based on the dictionary. Defaulting to Shift #1.')
        final_text = decrypted_results[0]

    try:
        # 최종 암호를 result.txt로 저장합니다.
        with open(RESULT_FILENAME, 'w', encoding='utf-8') as f:
            f.write(final_text)
        print(f"\n[SUCCESS] Decoded text saved to '{RESULT_FILENAME}'")
        print(f'  Final result: {final_text}')
    except IOError as e:
        print(f'[ERROR] Error writing result to file: {e}')




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