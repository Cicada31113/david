# mmc2.py
from __future__ import annotations
import json, time, threading
from collections import deque
from typing import Iterable  # 표준 타입 표기는 유지하지만 typing의 제네릭은 안 씀
from mmc1 import DummySensor  # 같은 디렉토리에 있다고 가정

class MissionComputer:
    def __init__(self, sensor: DummySensor) -> None:
        self.sensor = sensor
        self.env_values: dict[str, float | None] = {k: None for k in sensor.env_values.keys()}
        self._history: dict[str, deque[tuple[float, float]]] = {k: deque() for k in self.env_values}
        self._last_avg_print: float = time.time()

    def get_sensor_data(
        self,
        interval_sec: int = 5,
        log_sensor: bool = True,
        stop_event: object | None = None,
        stop_word: str | None = 'q',
    ) -> None:
        try:
            if stop_word:
                if stop_event is None:
                    stop_event = threading.Event()
                self._start_input_stop_thread(stop_event, stop_word)

            while not self._should_stop(stop_event):
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

    @staticmethod
    def _start_input_stop_thread(stop_event: threading.Event, stop_word: str = 'q') -> threading.Thread:
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

    @staticmethod
    def _should_stop(flag: object | None) -> bool:
        if flag is None:
            return False
        fn = getattr(flag, 'is_set', None)
        return bool(callable(fn) and fn())

    def _push_history(self, now: float, env: dict[str, float | None]) -> None:
        cutoff = now - 300.0
        for k, dq in self._history.items():
            v = env.get(k)
            if isinstance(v, (int, float)):
                dq.append((now, float(v)))
            while dq and dq[0][0] < cutoff:
                dq.popleft()

    def _compute_5min_avg(self, now: float) -> dict[str, float | None]:
        cutoff = now - 300.0
        out: dict[str, float | None] = {}
        for k, dq in self._history.items():
            while dq and dq[0][0] < cutoff:
                dq.popleft()
            if dq:
                s = sum(v for _, v in dq)
                out[k] = round(s / len(dq), 3)
            else:
                out[k] = None
        return out

if __name__ == '__main__':
    ds = DummySensor()
    mc = MissionComputer(ds)
    mc.get_sensor_data(interval_sec=5, log_sensor=True, stop_word='q')
