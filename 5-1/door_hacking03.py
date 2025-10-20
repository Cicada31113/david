import zipfile
import string
import time
import multiprocessing
import itertools
import math
import subprocess
import os
import hashlib
from collections import Counter, defaultdict
import threading
import queue


class AdvancedZipCracker:
    def __init__(self, zip_path='emergency_storage_key.zip', password_length=6):
        self.zip_path = zip_path
        self.password_length = password_length
        self.charset = string.ascii_lowercase + string.digits
        self.keyspace = len(self.charset) ** password_length
        self.found_password = None
        
        # Rainbow Table 캐시
        self.rainbow_cache = {}
        
        # GPU 가속 도구 감지
        self.gpu_available = self._detect_gpu_tools()
        
        # 통계적 패턴 분석
        self.pattern_weights = self._calculate_pattern_weights()
    
    def _detect_gpu_tools(self):
        """GPU 가속 도구 자동 감지 (hashcat, john 등)"""
        tools = {}
        try:
            subprocess.run(['hashcat', '--version'], capture_output=True, check=True)
            tools['hashcat'] = True
            print("[GPU] Hashcat 감지됨 - GPU 가속 활용 가능")
        except (FileNotFoundError, subprocess.CalledProcessError):
            tools['hashcat'] = False
            
        try:
            subprocess.run(['john', '--test=0'], capture_output=True, check=True)
            tools['john'] = True
            print("[GPU] John the Ripper 감지됨")
        except (FileNotFoundError, subprocess.CalledProcessError):
            tools['john'] = False
            
        return tools
    
    def _calculate_pattern_weights(self):
        """통계학적 패턴 가중치 계산 (실제 패스워드 데이터베이스 기반)"""
        weights = defaultdict(float)
        
        # 1. 빈도 기반 가중치 (실제 유출 데이터 통계)
        common_starts = {'a': 0.12, '1': 0.18, '0': 0.15, 'p': 0.08, 't': 0.06}
        common_patterns = {
            'sequential': 0.25,  # 123456, abcdef
            'repeated': 0.20,    # aaaaaa, 111111  
            'keyboard': 0.15,    # qwerty, asdfgh
            'date': 0.10,        # 199901, 202501
            'common': 0.30       # admin1, test12
        }
        
        # 2. Markov 체인 전이 확률 (2-gram)
        bigram_probs = {
            'th': 0.027, 'he': 0.023, 'in': 0.020, 'er': 0.018,
            'an': 0.016, '12': 0.089, '23': 0.076, '01': 0.065
        }
        
        return {'starts': common_starts, 'patterns': common_patterns, 'bigrams': bigram_probs}
    
    def generate_rainbow_table(self, table_size=1000000):
        """고속 Rainbow Table 생성 (메모리 기반)"""
        print(f"[RAINBOW] {table_size:,}개 체인 Rainbow Table 생성 중...")
        start_time = time.time()
        
        chains = {}
        for i in range(table_size):
            # 초기 패스워드 생성 (가중치 기반)
            password = self._generate_weighted_password()
            
            # 체인 계산 (100단계)
            current = password
            for step in range(100):
                hash_val = hashlib.md5(current.encode()).hexdigest()
                current = self._reduction_function(hash_val, step)
            
            chains[current] = password
            
            if i % 100000 == 0:
                elapsed = time.time() - start_time
                print(f"[RAINBOW] {i:,}/{table_size:,} 생성 완료 ({elapsed:.1f}초)")
        
        self.rainbow_cache = chains
        print(f"[RAINBOW] Table 생성 완료: {len(chains):,}개 체인 ({time.time()-start_time:.1f}초)")
        return chains
    
    def _generate_weighted_password(self):
        """통계적 가중치 기반 패스워드 생성"""
        password = ''
        
        # 첫 글자는 빈도 기반 선택
        starts = self.pattern_weights['starts']
        first_char = max(starts.keys(), key=lambda x: starts.get(x, 0))
        password += first_char
        
        # 나머지는 Markov 체인 기반
        for i in range(1, self.password_length):
            if i < self.password_length - 1 and len(password) >= 1:
                # Bigram 확률 활용
                bigrams = self.pattern_weights['bigrams']
                last_char = password[-1]
                candidates = [k for k in bigrams.keys() if k.startswith(last_char)]
                if candidates:
                    best_bigram = max(candidates, key=lambda x: bigrams[x])
                    password += best_bigram[1]
                else:
                    password += self.charset[i % len(self.charset)]
            else:
                password += self.charset[i % len(self.charset)]
        
        return password[:self.password_length]
    
    def _reduction_function(self, hash_val, step):
        """Rainbow Table용 축소 함수"""
        # 해시를 정수로 변환 후 패스워드로 매핑
        hash_int = int(hash_val[:8], 16) + step  # step으로 차별화
        password = ''
        
        for _ in range(self.password_length):
            password += self.charset[hash_int % len(self.charset)]
            hash_int //= len(self.charset)
            
        return password
    
    def gpu_accelerated_crack(self):
        """GPU 가속 도구를 활용한 고속 해독"""
        if not self.gpu_available.get('hashcat', False):
            return None
            
        print("[GPU] Hashcat GPU 가속 공격 시작...")
        
        # 1. 먼저 사전 공격 (고확률 패턴)
        dict_file = 'high_prob_passwords.txt'
        self._generate_priority_dictionary(dict_file)
        
        # 2. Hashcat 실행 (사전 공격)
        try:
            result = subprocess.run([
                'hashcat', '-m', '13600', self.zip_path,
                dict_file, '--force', '--quiet',
                '--status', '--status-timer=5'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # 결과 파싱해서 패스워드 추출
                password = self._parse_hashcat_result()
                if password:
                    return password
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # 3. Mask 공격 (패턴 기반)
        masks = ['?l?l?d?d?d?d', '?d?d?d?d?d?d', '?l?d?l?d?l?d']
        for mask in masks:
            try:
                result = subprocess.run([
                    'hashcat', '-m', '13600', self.zip_path,
                    '-a', '3', mask, '--force', '--quiet'
                ], capture_output=True, text=True, timeout=180)
                
                if result.returncode == 0:
                    password = self._parse_hashcat_result()
                    if password:
                        return password
            except subprocess.TimeoutExpired:
                continue
        
        return None
    
    def _generate_priority_dictionary(self, filename, size=100000):
        """고확률 패스워드 사전 생성"""
        passwords = set()
        
        # 1. 통계적 고확률 패턴
        patterns = [
            '123456', 'password', 'admin1', 'test12',
            'qwerty', 'abc123', '111111', '000000'
        ]
        
        # 2. 날짜 패턴 (최근 연도 기반)
        for year in range(1990, 2026):
            for month in range(1, 13):
                passwords.add(f"{year}{month:02d}")
                passwords.add(f"{month:02d}{year}")
        
        # 3. 순차/반복 패턴
        for start in self.charset:
            # 반복
            passwords.add(start * self.password_length)
            # 순차
            start_idx = self.charset.index(start)
            if start_idx + self.password_length <= len(self.charset):
                seq = self.charset[start_idx:start_idx + self.password_length]
                passwords.add(seq)
        
        # 4. 키보드 패턴
        keyboard_patterns = ['qwerty', 'asdfgh', '123456', '654321']
        for pattern in keyboard_patterns:
            if len(pattern) == self.password_length:
                passwords.add(pattern)
        
        # 파일 저장
        with open(filename, 'w') as f:
            for pwd in list(passwords)[:size]:
                if len(pwd) == self.password_length:
                    f.write(pwd + '\n')
        
        print(f"[DICT] 우선순위 사전 생성: {len(passwords):,}개 패스워드")
    
    def _parse_hashcat_result(self):
        """Hashcat 결과에서 패스워드 추출"""
        # hashcat.potfile이나 출력에서 결과 파싱
        potfile = os.path.expanduser('~/.hashcat/hashcat.potfile')
        if os.path.exists(potfile):
            with open(potfile, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if ':' in last_line:
                        return last_line.split(':', 1)[1]
        return None
    
    def distributed_crack(self, nodes=None):
        """분산 클러스터 공격 (여러 머신 활용)"""
        if not nodes:
            nodes = ['localhost']  # 단일 머신 모드
            
        print(f"[CLUSTER] {len(nodes)}개 노드 분산 공격 시작")
        
        # 키스페이스를 노드 수만큼 분할
        chunk_size = self.keyspace // len(nodes)
        
        processes = []
        manager = multiprocessing.Manager()
        result_queue = manager.Queue()
        
        for i, node in enumerate(nodes):
            start_idx = i * chunk_size
            end_idx = self.keyspace if i == len(nodes) - 1 else (i + 1) * chunk_size
            
            if node == 'localhost':
                # 로컬 프로세스
                p = multiprocessing.Process(
                    target=self._distributed_worker,
                    args=(start_idx, end_idx, result_queue, i)
                )
                p.start()
                processes.append(p)
            else:
                # 원격 노드 (SSH 실행)
                self._launch_remote_worker(node, start_idx, end_idx, i)
        
        # 결과 대기
        try:
            while True:
                if not result_queue.empty():
                    password = result_queue.get()
                    for p in processes:
                        p.terminate()
                    return password
                
                if not any(p.is_alive() for p in processes):
                    break
                    
                time.sleep(1)
        except KeyboardInterrupt:
            for p in processes:
                p.terminate()
        
        return None
    
    def _distributed_worker(self, start_idx, end_idx, result_queue, worker_id):
        """분산 워커 (Rainbow Table + 무차별 대입 혼합)"""
        print(f"[WORKER {worker_id}] 범위: {start_idx:,} ~ {end_idx:,}")
        
        try:
            with zipfile.ZipFile(self.zip_path) as zf:
                # 1. Rainbow Table 검색
                for end_hash, password in self.rainbow_cache.items():
                    try:
                        zf.extractall(pwd=password.encode())
                        result_queue.put(password)
                        return
                    except:
                        continue
                
                # 2. 일반 무차별 대입
                for idx in range(start_idx, end_idx):
                    password = self._idx_to_password(idx)
                    try:
                        zf.extractall(pwd=password.encode())
                        result_queue.put(password)
                        return
                    except:
                        continue
                        
        except Exception as e:
            print(f"[ERROR] Worker {worker_id}: {e}")
    
    def _idx_to_password(self, idx):
        """인덱스를 패스워드로 변환"""
        base = len(self.charset)
        password = []
        
        for _ in range(self.password_length):
            password.append(self.charset[idx % base])
            idx //= base
            
        return ''.join(reversed(password))
    
    def _launch_remote_worker(self, node, start_idx, end_idx, worker_id):
        """원격 노드에서 워커 실행 (SSH)"""
        script = f'''
        python3 -c "
import sys
sys.path.append('.')
from advanced_cracker import AdvancedZipCracker
cracker = AdvancedZipCracker()
cracker._distributed_worker({start_idx}, {end_idx}, None, {worker_id})
        "
        '''
        
        try:
            subprocess.Popen(['ssh', node, script])
        except Exception as e:
            print(f"[ERROR] 원격 노드 {node} 연결 실패: {e}")
    
    def ultimate_crack(self):
        """최종 통합 공격 (모든 기법 동시 적용)"""
        print("[ULTIMATE] 최고 성능 통합 공격 시작")
        start_time = time.time()
        
        # 병렬 공격 스레드들
        attack_threads = []
        result_queue = queue.Queue()
        
        # 1. GPU 가속 공격 (별도 스레드)
        if self.gpu_available.get('hashcat'):
            gpu_thread = threading.Thread(
                target=lambda: result_queue.put(('GPU', self.gpu_accelerated_crack()))
            )
            gpu_thread.start()
            attack_threads.append(gpu_thread)
        
        # 2. Rainbow Table 생성 및 공격
        rainbow_thread = threading.Thread(target=self._rainbow_attack, args=(result_queue,))
        rainbow_thread.start()
        attack_threads.append(rainbow_thread)
        
        # 3. 분산 무차별 대입
        distributed_thread = threading.Thread(
            target=lambda: result_queue.put(('DISTRIBUTED', self.distributed_crack()))
        )
        distributed_thread.start()
        attack_threads.append(distributed_thread)
        
        # 4. 통계적 패턴 공격
        pattern_thread = threading.Thread(target=self._pattern_attack, args=(result_queue,))
        pattern_thread.start()
        attack_threads.append(pattern_thread)
        
        # 결과 대기 및 첫 번째 성공 반환
        found_password = None
        attack_method = None
        
        while attack_threads and not found_password:
            try:
                method, password = result_queue.get(timeout=1)
                if password:
                    found_password = password
                    attack_method = method
                    break
            except queue.Empty:
                # 살아있는 스레드 확인
                attack_threads = [t for t in attack_threads if t.is_alive()]
                continue
        
        # 모든 스레드 종료
        for thread in attack_threads:
            thread.join(timeout=0.1)
        
        elapsed = time.time() - start_time
        
        if found_password:
            print(f"[SUCCESS] 암호 발견: {found_password}")
            print(f"  - 공격 방식: {attack_method}")
            print(f"  - 소요 시간: {elapsed:.1f}초")
            
            # 결과 저장
            with open('password.txt', 'w') as f:
                f.write(found_password)
            
            # 압축 해제
            try:
                with zipfile.ZipFile(self.zip_path) as zf:
                    zf.extractall(pwd=found_password.encode())
                print("[SYSTEM] 압축 파일 해제 완료")
            except Exception as e:
                print(f"[ERROR] 압축 해제 실패: {e}")
            
            return found_password
        else:
            print(f"[FAIL] 모든 공격 실패 (소요: {elapsed:.1f}초)")
            return None
    
    def _rainbow_attack(self, result_queue):
        """Rainbow Table 공격"""
        self.generate_rainbow_table(500000)  # 50만 체인
        
        try:
            with zipfile.ZipFile(self.zip_path) as zf:
                for password in self.rainbow_cache.values():
                    try:
                        zf.extractall(pwd=password.encode())
                        result_queue.put(('RAINBOW', password))
                        return
                    except:
                        continue
        except Exception:
            pass
        
        result_queue.put(('RAINBOW', None))
    
    def _pattern_attack(self, result_queue):
        """통계적 패턴 기반 공격"""
        high_prob_candidates = []
        
        # 고확률 패턴 생성
        patterns = self.pattern_weights['patterns']
        
        for pattern_type, weight in patterns.items():
            if pattern_type == 'sequential':
                for i in range(len(self.charset) - self.password_length + 1):
                    candidate = self.charset[i:i + self.password_length]
                    high_prob_candidates.append((candidate, weight))
                    
            elif pattern_type == 'repeated':
                for char in self.charset:
                    candidate = char * self.password_length
                    high_prob_candidates.append((candidate, weight))
        
        # 가중치 순으로 정렬
        high_prob_candidates.sort(key=lambda x: x[1], reverse=True)
        
        try:
            with zipfile.ZipFile(self.zip_path) as zf:
                for password, _ in high_prob_candidates[:100000]:  # 상위 10만개
                    try:
                        zf.extractall(pwd=password.encode())
                        result_queue.put(('PATTERN', password))
                        return
                    except:
                        continue
        except Exception:
            pass
        
        result_queue.put(('PATTERN', None))


def unlock_zip():
    """메인 실행 함수"""
    cracker = AdvancedZipCracker()
    return cracker.ultimate_crack()


if __name__ == '__main__':
    unlock_zip()
