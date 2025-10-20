# mmc4.py
from __future__ import annotations
import json, time, threading, multiprocessing
from mmc1 import DummySensor
from mmc3 import MissionComputerV2 as MissionComputer  # 모든 기능 포함 버전 사용

def _run_info_process(mc: MissionComputer, stop_event: object) -> None:
    mc.get_mission_computer_info(interval_sec=20, stop_event=stop_event, stop_word=None)

def _run_load_process(mc: MissionComputer, stop_event: object) -> None:
    mc.get_mission_computer_load(interval_sec=20, stop_event=stop_event, stop_word=None)

def _run_sensor_process(mc: MissionComputer, stop_event: object) -> None:
    mc.get_sensor_data(interval_sec=5, log_sensor=True, stop_event=stop_event, stop_word=None)

if __name__ == '__main__':
    multiprocessing.freeze_support()

    # 1) 단일 실행 예시
    ds = DummySensor()
    mc = MissionComputer(ds)

    print("\n[Sensor stream] type 'q'/'quit' or Ctrl+C to stop")
    mc.get_sensor_data(interval_sec=5, log_sensor=True, stop_word='q')

    print("\n[System info stream] type 'q'/'quit' or Ctrl+C to stop")
    mc.get_mission_computer_info(interval_sec=20, stop_word='q')

    print("\n[Load stream] type 'q'/'quit' or Ctrl+C to stop")
    mc.get_mission_computer_load(interval_sec=20, stop_word='q')

    # 2) 멀티스레드 데모
    print("\n[Multi-thread demo] type 'q'/'quit' to stop all threads")
    thr_stop = threading.Event()
    mc_thr = MissionComputer(DummySensor())
    threads = [
        threading.Thread(target=mc_thr.get_sensor_data, kwargs={'interval_sec': 5, 'log_sensor': False, 'stop_event': thr_stop, 'stop_word': 'q'}),
        threading.Thread(target=mc_thr.get_mission_computer_info, kwargs={'interval_sec': 20, 'stop_event': thr_stop, 'stop_word': 'q'}),
        threading.Thread(target=mc_thr.get_mission_computer_load, kwargs={'interval_sec': 20, 'stop_event': thr_stop, 'stop_word': 'q'}),
    ]
    # 입력 스레드 (공유) — 'q'/'quit'으로 모두 종료
    def _input_stop_threads() -> None:
        try:
            while any(t.is_alive() for t in threads):
                try:
                    text = input().strip().lower()
                except EOFError:
                    break
                if text in ('q', 'quit'):
                    print('System stoped....')
                    thr_stop.set()
                    break
        except Exception:
            pass
    for t in threads: t.start()
    kb_t = threading.Thread(target=_input_stop_threads, daemon=True); kb_t.start()
    try:
        while any(t.is_alive() for t in threads):
            time.sleep(1)
    except KeyboardInterrupt:
        print('System stoped....'); thr_stop.set()
    finally:
        thr_stop.set()
        for t in threads: t.join()

    # 3) 멀티프로세스 데모
    print("\n[Multi-process demo] Ctrl+C or type 'q'/'quit' to stop all processes")
    m1, m2, m3 = MissionComputer(DummySensor()), MissionComputer(DummySensor()), MissionComputer(DummySensor())
    pevents = [multiprocessing.Event() for _ in range(3)]
    procs = [
        multiprocessing.Process(target=_run_info_process, args=(m1, pevents[0])),
        multiprocessing.Process(target=_run_load_process, args=(m2, pevents[1])),
        multiprocessing.Process(target=_run_sensor_process, args=(m3, pevents[2])),
    ]
    def _input_stop_processes() -> None:
        try:
            while any(p.is_alive() for p in procs):
                try:
                    text = input().strip().lower()
                except EOFError:
                    break
                if text in ('q', 'quit'):
                    print('System stoped....')
                    for e in pevents: e.set()
                    break
        except Exception:
            pass
    for p in procs: p.start()
    kb_p = threading.Thread(target=_input_stop_processes, daemon=True); kb_p.start()
    try:
        while any(p.is_alive() for p in procs):
            time.sleep(1)
    except KeyboardInterrupt:
        print('System stoped....')
        for e in pevents: e.set()
    finally:
        for e in pevents: e.set()
        for p in procs:
            p.join(timeout=5)
            if p.is_alive():
                p.terminate()








