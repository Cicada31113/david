from __future__ import annotations
import json
import multiprocessing
import os
import platform
import random
import threading
import time
from collections import deque
from datetime import datetime


class DummySensor:
    LOG_PATH = 'mission_env.log'

    def __init__(self) -> None:
        self.env_values: dict[str, float | None] = {
            'mars_base_internal_temperature': None,
            'mars_base_external_temperature': None,
            'mars_base_internal_humidity': None,
            'mars_base_external_illuminance': None,
            'mars_base_internal_co2': None,
            'mars_base_internal_oxygen': None,
        }

    def set_env(self) -> None:
        self.env_values['mars_base_internal_temperature'] = round(random.uniform(18, 30), 2)
        self.env_values['mars_base_external_temperature'] = round(random.uniform(0, 21), 2)
        self.env_values['mars_base_internal_humidity'] = round(random.uniform(50, 60), 2)
        self.env_values['mars_base_external_illuminance'] = round(random.uniform(500, 715), 2)
        self.env_values['mars_base_internal_co2'] = round(random.uniform(0.02, 0.1), 4)
        self.env_values['mars_base_internal_oxygen'] = round(random.uniform(4, 7), 2)

    def get_env(self, *, log: bool = True) -> dict[str, float | None]:
        if log:
            self._log_env(self.env_values)
        return self.env_values

    def _log_env(self, env: dict[str, float | None]) -> None:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        header = (
            'datetime,'
            'mars_base_internal_temperature,'
            'mars_base_external_temperature,'
            'mars_base_internal_humidity,'
            'mars_base_external_illuminance,'
            'mars_base_internal_co2,'
            'mars_base_internal_oxygen'
        )
        line = (
            f"{ts},"
            f"{env['mars_base_internal_temperature']},"
            f"{env['mars_base_external_temperature']},"
            f"{env['mars_base_internal_humidity']},"
            f"{env['mars_base_external_illuminance']},"
            f"{env['mars_base_internal_co2']},"
            f"{env['mars_base_internal_oxygen']}"
        )
        file_exists = os.path.exists(self.LOG_PATH)
        with open(self.LOG_PATH, mode='a', encoding='utf-8') as log_file:
            if not file_exists:
                log_file.write(header + '\n')
            log_file.write(line + '\n')


class MissionComputer:
    def __init__(self, sensor: DummySensor) -> None:
        self.sensor = sensor
        self.env_values: dict[str, float | None] = {
            'mars_base_internal_temperature': None,
            'mars_base_external_temperature': None,
            'mars_base_internal_humidity': None,
            'mars_base_external_illuminance': None,
            'mars_base_internal_co2': None,
            'mars_base_internal_oxygen': None,
        }
        # 5분 슬라이딩 윈도우: 각 키별 (timestamp, value) = [float, float]    
        self._history: dict[str, deque[tuple[float, float]]] = {
            k: deque() for k in self.env_values.keys()               # .keys() = 딕셔너리 안에  들어있는 모든 KEY 를 모아서 보여줌.
        }
        self._last_avg_print: float = time.time()                    # .time() = time.time() 지금 시각을 Epoch time으로 반환, 여기서 float은 타입힌트

    # -------------------
    # 공개 API
    # -------------------
    def get_sensor_data(
        self,
        interval_sec: int = 5,
        log_sensor: bool = True,
        stop_event: object | None = None,              # "stop_event"는 object 타입이거나 None일 수 있다", object는 파이썬의 모든 클래스와 데이터가 상속받는 최상위(base)타입. object를 쓰면, 여기에는 어떤 객체든 들어 올 수 있다는 포괄적인 선언.
        stop_key: str = 'q',
        stop_word: str | None = 'q',  # 기본 'q', 'quit'도 허용
    ) -> None:
        try:
            if stop_word:
                if stop_event is None:                       
                    stop_event = threading.Event()                  # Event는 스레드 간 신호를 주고받는 도구. 스레드끼리 공유하는 깃발(flag) 역할. 여기선 stop_event = 스레드 간 "멈춰야한다"는 신호깃발
                self._start_input_stop_thread(stop_event, stop_word)

            while not self._should_stop(stop_event):
                if self._key_pressed(stop_key):
                    break

                self.sensor.set_env()
                data = self.sensor.get_env(log=log_sensor)
                self.env_values.update(data)
                print(json.dumps(self.env_values, ensure_ascii=False))

                now = time.time()
                self._push_history(now, self.env_values)
                if now - self._last_avg_print >= 300:
                    avg = self._compute_5min_avg(now)
                    print(json.dumps({'5min_avg': avg}, ensure_ascii=False))
                    self._last_avg_print = now

                if self._should_stop(stop_event):
                    break
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            print('System stoped....')

    def get_mission_computer_info(
        self,
        interval_sec: int = 20,
        stop_event: object | None = None,
        stop_key: str = 'q',
        stop_word: str | None = 'q',
    ) -> None:
        try:
            if stop_word:
                if stop_event is None:
                    stop_event = threading.Event()
                self._start_input_stop_thread(stop_event, stop_word)

            while not self._should_stop(stop_event):
                if self._key_pressed(stop_key):
                    break
                allowed = self._load_settings().get('info')
                info = self._collect_system_info()
                if allowed:
                    info = {k: v for k, v in info.items() if k in allowed}
                print(json.dumps(info, ensure_ascii=False))
                if self._should_stop(stop_event):
                    break
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            print('System stoped....')

    def get_mission_computer_load(
        self,
        interval_sec: int = 20,
        stop_event: object | None = None,
        stop_key: str = 'q',
        stop_word: str | None = 'q',
    ) -> None:
        try:
            if stop_word:
                if stop_event is None:
                    stop_event = threading.Event()
                self._start_input_stop_thread(stop_event, stop_word)

            while not self._should_stop(stop_event):
                if self._key_pressed(stop_key):
                    break
                allowed = self._load_settings().get('load')
                load = self._collect_load_info()
                if allowed:
                    load = {k: v for k, v in load.items() if k in allowed}
                print(json.dumps(load, ensure_ascii=False))
                if self._should_stop(stop_event):
                    break
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            print('System stoped....')

    # -------------------
    # 내부 유틸
    # -------------------
    @staticmethod
    def _should_stop(flag: object | None) -> bool:
        if flag is None:
            return False
        is_set = getattr(flag, 'is_set', None)        # (객체, '속성이름', '기본값)
        if callable(is_set):
            try:
                return bool(is_set())
            except Exception:
                return False
        return False

    @staticmethod
    def _key_pressed(stop_key: str) -> bool:
        # msvcrt 없이 크로스플랫폼 유지: 입력 스레드 방식만 사용
        return False

    @staticmethod
    def _start_input_stop_thread(stop_event: threading.Event, stop_word: str = 'q') -> threading.Thread:
        """콘솔에서 'q' 또는 'quit' 입력 시 stop_event.set()"""
        def _wait_input() -> None:
            try:
                while not stop_event.is_set():
                    try:
                        text = input().strip().lower()
                    except EOFError:
                        break
                    if text in ('q', 'quit'):
                        print('System stoped....')
                        stop_event.set()
                        break
            except Exception:
                pass

        t = threading.Thread(target=_wait_input, name='InputStopThread', daemon=True)
        t.start()
        return t

    def _push_history(self, now: float, env: dict[str, float | None]) -> None:
        cutoff = now - 300.0
        for k, dq in self._history.items():
            v = env.get(k)
            if isinstance(v, (int, float)):
                dq.append((now, float(v)))
            while dq and dq[0][0] < cutoff:
                dq.popleft()

    def _compute_5min_(self, now: float) -> dict[str, float | None]:
        cutoff = now - 300.0
        result: dict[str, float | None] = {}
        for k, dq in self._history.items():
            while dq and dq[0][0] < cutoff:
                dq.popleft()
            if dq:
                s = sum(v for _, v in dq)
                result[k] = round(s / len(dq), 3)
            else:
                result[k] = None
        return result

    # -------------------
    # 시스템 정보/부하 수집(표준 라이브러리만)
    # -------------------
    def _collect_system_info(self) -> dict[str, str | int | float]:
        try:
            metrics = {
                'os': platform.system(),
                'os_version': platform.version(),
                'cpu_model': platform.processor() or platform.machine(),
                'cpu_core_count': os.cpu_count() or 0,
                'memory_total_gb': self._get_total_memory_gb(),
            }
        except Exception as exc:
            metrics = {'error': f'system info unavailable: {exc}'}
        return metrics

    @staticmethod
    def _get_total_memory_gb() -> float | str:
        # POSIX: sysconf
        if hasattr(os, 'sysconf'):
            try:
                page_size = os.sysconf('SC_PAGE_SIZE')      # bytes per page
                page_count = os.sysconf('SC_PHYS_PAGES')    # number of pages
                total_bytes = page_size * page_count
                return round(total_bytes / 1024 ** 3, 2)
            except (AttributeError, OSError, ValueError):
                pass
        # Windows: GlobalMemoryStatusEx
        if os.name == 'nt':
            try:
                import ctypes

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong),
                        ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong),
                        ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong),
                        ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
                    ]

                status = MEMORYSTATUSEX()
                status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                    return round(status.ullTotalPhys / 1024 ** 3, 2)
            except Exception:
                pass
        return 'unknown'

    @staticmethod
    def _collect_load_info() -> dict[str, float | str]:
        # psutil 없이: getloadavg 기반 CPU 근사치, 메모리%는 알 수 없으면 'unknown'
        load: dict[str, float | str] = {
            'cpu_usage_percent': 'unknown',
            'memory_usage_percent': 'unknown'
        }
        if hasattr(os, 'getloadavg'):
            try:
                avg1, _, _ = os.getloadavg()         # 1분 평균 run-queue
                cores = os.cpu_count() or 1
                load['cpu_usage_percent'] = round(avg1 / cores * 100, 2)
            except (OSError, ValueError):
                pass
        return load

    # -------------------
    # setting.txt 필터링
    # -------------------
    @staticmethod
    def _load_settings(path: str = 'setting.txt') -> dict[str, set[str]]:
        """예:
        info=os,os_version,cpu_model,cpu_core_count,memory_total_gb
        load=cpu_usage_percent,memory_usage_percent
        """
        result: dict[str, set[str]] = {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith('#'):
                        continue
                    if s.startswith('info='):
                        result['info'] = set(x.strip() for x in s[5:].split(',') if x.strip())
                    elif s.startswith('load='):
                        result['load'] = set(x.strip() for x in s[5:].split(',') if x.strip())
        except FileNotFoundError:
            pass
        return result


# -------------------
# 멀티프로세스 데모용 래퍼
# -------------------
def _run_info_process(mc: MissionComputer, stop_event: object) -> None:
    mc.get_mission_computer_info(interval_sec=20, stop_event=stop_event, stop_word=None)


def _run_load_process(mc: MissionComputer, stop_event: object) -> None:
    mc.get_mission_computer_load(interval_sec=20, stop_event=stop_event, stop_word=None)


def _run_sensor_process(mc: MissionComputer, stop_event: object) -> None:
    mc.get_sensor_data(interval_sec=5, log_sensor=True, stop_event=stop_event, stop_word=None)


if __name__ == '__main__':
    multiprocessing.freeze_support()

    ds = DummySensor()
    ds.set_env()
    env = ds.get_env(log=True)
    print(json.dumps(env, ensure_ascii=False, indent=2))

    print("\n[MissionComputer streaming] type 'q'/'quit' or Ctrl+C to stop")
    RunComputer = MissionComputer(ds)
    RunComputer.get_sensor_data(interval_sec=5, log_sensor=True, stop_word='q')

    print("\n[MissionComputer system info] type 'q'/'quit' or Ctrl+C to stop")
    RunComputer.get_mission_computer_info(interval_sec=20, stop_word='q')

    print("\n[MissionComputer load info] type 'q'/'quit' or Ctrl+C to stop")
    RunComputer.get_mission_computer_load(interval_sec=20, stop_word='q')

