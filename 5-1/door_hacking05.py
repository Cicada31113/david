import itertools
import string
import time
import zipfile
import multiprocessing as mp
import os

# --- 상수 정의 ---
ZIP_FILENAME = 'emergency_storage_key.zip'
TARGET_FILE_IN_ZIP = 'password.txt' # ZIP 파일 안의 암호화된 파일
ZIP_PASSWORD_FILENAME = 'zip_password.txt' # ZIP을 푼 6자리 암호를 저장할 파일
CAESAR_CIPHER_FILENAME = 'password.txt' # 해독된 카이사르 암호문이 저장될 파일
RESULT_FILENAME = 'result.txt'
CHARSET = string.ascii_lowercase + string.digits
PW_LENGTH = 6


def find_zip_entry_password_worker(password_queue, found_queue, attempts_queue):
    """
    워커 프로세스: ZIP 파일 안의 특정 파일('password.txt')을 읽기 위한 암호를 찾습니다.
    """
    try:
        zip_file = zipfile.ZipFile(ZIP_FILENAME)
    except (FileNotFoundError, zipfile.BadZipFile) as e:
        # 파일이 없거나 손상된 경우, 이 워커는 작업을 중단합니다.
        # 메인 프로세스에서 파일 존재 여부를 먼저 확인하므로, 이 경우는 드뭅니다.
        return

    local_attempts = 0
    while not found_event.is_set():
        try:
            # 큐에서 작업할 비밀번호를 가져옵니다. 
            password = password_queue.get(timeout=0.1)
            if password is None:  # 작업 종료 신호
                break
        except mp.queues.Empty:
            # 큐가 비어있으면 작업이 끝난 것으로 간주 
            break

        try:
            # 비밀번호를 바이트로 인코딩하여 압축 해제 시도
            decrypted_content = zip_file.read(TARGET_FILE_IN_ZIP, pwd=password.encode('utf-8'))
            
            # 성공 시, 다른 프로세스에 알리기 위해 이벤트를 설정합니다.
            if not found_event.is_set():
                found_event.set()
                # 찾은 비밀번호를 큐에 넣어 메인 프로세스에 전달
                found_queue.put((password, decrypted_content))
            break  # 성공했으므로 루프 종료
        except (RuntimeError, zipfile.BadZipFile):
            # 잘못된 비밀번호일 경우, 시도 횟수를 늘리고 계속 진행 
            local_attempts += 1
            if local_attempts % 20000 == 0:  # 너무 잦은 업데이트 방지
                attempts_queue.put(local_attempts)
                local_attempts = 0
        except Exception:
            # 기타 예외 발생 시에도 계속 진행 
            continue
    
    # 남은 시도 횟수 보고
    if local_attempts > 0:
        attempts_queue.put(local_attempts)


def unlock_zip():
    """
    (문제 1) emergency_storage_key.zip 안의 password.txt 파일 암호를 찾아 해제합니다.
    성공 시, 6자리 암호는 zip_password.txt에, 해독된 내용은 password.txt에 저장합니다.
    """
    if not os.path.exists(ZIP_FILENAME):
        print(f'Error: {ZIP_FILENAME} not found. Please place it in the same directory.')
        return False

    start_time = time.time()
    print(f"Starting password search for '{TARGET_FILE_IN_ZIP}' inside '{ZIP_FILENAME}'...")

    password_queue = mp.Queue()
    found_queue = mp.Queue()
    attempts_queue = mp.Queue()
    found_event = mp.Event()

    # 모든 비밀번호 조합을 생성하여 큐에 추가
    print('Generating and queuing all possible passwords...')
    all_passwords = (''.join(p) for p in itertools.product(CHARSET, repeat=PW_LENGTH))
    for p in all_passwords:
        password_queue.put(p)

    num_workers = mp.cpu_count()
    print(f'Starting {num_workers} worker processes...')
    
    processes = []
    for _ in range(num_workers):
        # 각 워커가 종료 신호를 받을 수 있도록 None 추가
        password_queue.put(None)
        p = mp.Process(target=find_zip_entry_password_worker, args=(password_queue, found_queue, attempts_queue))
        processes.append(p)
        p.start()

    total_attempts = 0
    found_password = None

    # 메인 프로세스는 진행 상황을 모니터링
    while any(p.is_alive() for p in processes):
        if found_event.is_set() and found_password is None:
            # 암호를 찾았다는 신호가 오면, 큐에서 암호를 가져옴
            found_result = found_queue.get()
            # 다른 프로세스들이 종료되도록 큐를 비웁니다.
            while not password_queue.empty():
                try:
                    password_queue.get_nowait()
                except mp.queues.Empty:
                    break
            break

        try:
            # 워커들이 보고하는 시도 횟수를 집계
            attempt_count = attempts_queue.get(timeout=1)
            total_attempts += attempt_count
            elapsed_time = time.time() - start_time
            print(f'\rAttempts: {total_attempts:,}, Elapsed: {elapsed_time:.2f}s', end='', flush=True)
        except mp.queues.Empty:
            continue

    for p in processes:
        p.terminate()
        p.join()

    elapsed_time = time.time() - start_time
    print()  # 줄바꿈

    if found_result:
        zip_password, file_content = found_result
        print('\n' + '=' * 40)
        print(f"Success! Password for '{TARGET_FILE_IN_ZIP}' found: {zip_password}")
        print(f'Total attempts: {total_attempts:,}')
        print(f'Elapsed time: {elapsed_time:.2f} seconds')
        print('=' * 40)
        try:
            # 문제 1 요구사항: 암호를 password.txt로 저장
            # (여기서는 zip_password.txt로 저장하여 명확히 구분)
            with open(ZIP_PASSWORD_FILENAME, 'w', encoding='utf-8') as f:
                f.write(zip_password)
            print(f"ZIP entry password successfully saved to '{ZIP_PASSWORD_FILENAME}'")

            # 압축 해제된 파일 내용(카이사르 암호문)을 password.txt에 저장
            with open(CAESAR_CIPHER_FILENAME, 'w', encoding='utf-8') as f:
                f.write(file_content.decode('utf-8'))
            print(f"Decrypted content saved to '{CAESAR_CIPHER_FILENAME}' for the next step.")
            return True
        except IOError as e:
            print(f'Error writing files: {e}')
            return False
    else:
        print('\nPassword not found after checking all combinations.')
        return False


def caesar_cipher_decode(target_text):
    """
    (문제 2) 주어진 텍스트(카이사르 암호문)를 해독하고 결과를 result.txt에 저장합니다.
    """
    print('\n' + '=' * 40)
    print('Starting Caesar cipher decoding...')
    print(f'Original text: {target_text}')
    print('=' * 40)

    decrypted_results = []
    for shift in range(26):
        result = ''
        for char in target_text:
            if 'a' <= char <= 'z':
                shifted_char_code = ord(char) - shift
                if shifted_char_code < ord('a'):
                    shifted_char_code += 26
                result += chr(shifted_char_code)
            else:
                result += char
        
        decrypted_results.append(result)
        # 사용자가 1부터 26까지 입력하는 것을 고려하여 shift+1로 출력
        print(f'Shift #{shift + 1:02d}: {result}')
        
    while True:
        try:
            user_input = input(f'\nEnter the correct shift number to save the result (1-26): ')
            correct_shift = int(user_input)
            
            if 1 <= correct_shift <= 26:
                final_text = decrypted_results[correct_shift - 1]
                
                try:
                    # 최종 암호를 result.txt로 저장
                    with open(RESULT_FILENAME, 'w', encoding='utf-8') as f:
                        f.write(final_text)
                    print(f"Decoded text saved to '{RESULT_FILENAME}'")
                    print(f'Final result: {final_text}')
                    break
                except IOError as e:
                    print(f'Error writing result to file: {e}')
                    break
            else:
                print('Invalid number. Please enter a number between 1 and 26.')
        except ValueError:
            print('Invalid input. Please enter a number.')


def main():
    """전체 과제 실행을 관리하는 메인 함수"""
    # --- 문제 1: ZIP 파일 안의 파일 암호 풀기 ---
    # 카이사르 암호문이 담긴 password.txt가 없으면 암호 풀기를 시도합니다.
    if not os.path.exists(CAESAR_CIPHER_FILENAME):
        # 멀티프로세싱을 사용하려면 __name__ == '__main__' 블록 안에서 실행해야 합니다.
        if not unlock_zip():
            print('Failed to unlock the ZIP file entry. Exiting.')
            return
    else:
        print(f"'{CAESAR_CIPHER_FILENAME}' already exists. Skipping ZIP entry unlocking.")

    # --- 문제 2: 카이사르 암호 해독 ---
    try:
        with open(CAESAR_CIPHER_FILENAME, 'r', encoding='utf-8') as f:
            encrypted_password = f.read().strip()
        
        if encrypted_password:
            caesar_cipher_decode(encrypted_password)
        else:
            print(f'Error: {CAESAR_CIPHER_FILENAME} is empty.')
            
    except FileNotFoundError:
        print(f"Error: '{CAESAR_CIPHER_FILENAME}' not found.")
        print('Please run the unlock_zip() part first or create the file manually.')
    except Exception as e:
        print(f'An error occurred while reading the password file: {e}')

if __name__ == '__main__':
    main()
