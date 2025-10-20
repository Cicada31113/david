# mmc3.py
from __future__ import annotations
import os, platform, json, time, threading
from mmc1 import DummySensor
from mmc2 import MissionComputer  # 히스토리/평균 로직 재사용

class MissionComputerV2(MissionComputer):
    def get_mission_computer_info(
        self,
        interval_sec: int = 20,
        stop_event: object | None = None,
        stop_word: str | None = 'q',
    ) -> None:
        try:
            if stop_word:
                if stop_event is None:
                    stop_event = threading.Event()
                self._start_input_stop_thread(stop_event, stop_word)
            while not self._should_stop(stop_event):
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
        stop_word: str | None = 'q',
    ) -> None:
        try:
            if stop_word:
                if stop_event is None:
                    stop_event = threading.Event()
                self._start_input_stop_thread(stop_event, stop_word)
            while not self._should_stop(stop_event):
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

    def _collect_system_info(self) -> dict[str, str | int | float]:
        try:
            return {
                'os': platform.system(),
                'os_version': platform.version(),
                'cpu_model': platform.processor() or platform.machine(),
                'cpu_core_count': os.cpu_count() or 0,
                'memory_total_gb': self._get_total_memory_gb(),
            }
        except Exception as exc:
            return {'error': f'system info unavailable: {exc}'}

    @staticmethod
    def _get_total_memory_gb() -> float | str:
        if hasattr(os, 'sysconf'):
            try:
                page_size = os.sysconf('SC_PAGE_SIZE')
                page_count = os.sysconf('SC_PHYS_PAGES')
                total_bytes = page_size * page_count
                return round(total_bytes / 1024**3, 2)
            except (AttributeError, OSError, ValueError):
                pass
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
                    return round(status.ullTotalPhys / 1024**3, 2)
            except Exception:
                pass
        return 'unknown'

    @staticmethod
    def _collect_load_info() -> dict[str, float | str]:
        load: dict[str, float | str] = {'cpu_usage_percent': 'unknown', 'memory_usage_percent': 'unknown'}
        if hasattr(os, 'getloadavg'):
            try:
                avg1, _, _ = os.getloadavg()
                cores = os.cpu_count() or 1
                load['cpu_usage_percent'] = round(avg1 / cores * 100, 2)
            except (OSError, ValueError):
                pass
        return load

    @staticmethod
    def _load_settings(path: str = 'setting.txt') -> dict[str, set[str]]:
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

if __name__ == '__main__':
    ds = DummySensor()
    mc = MissionComputerV2(ds)
    print('[info stream] type q/quit')
    mc.get_mission_computer_info(interval_sec=20, stop_word='q')

