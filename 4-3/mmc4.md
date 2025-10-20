# MMC4: 멀티쓰레드/멀티프로세스 도식화(이벤트 기반 종료)

## 1) 멀티쓰레드 구성
```text
메인 스레드
   ├─ thread A: get_sensor_data(interval=5s, log=False)
   ├─ thread B: get_mission_computer_info(interval=20s)
   └─ thread C: get_mission_computer_load(interval=20s)

공유 종료 신호: thread_stop_event (threading.Event)
   · any 스레드가 실행 중 → 메인 스레드는 주기적으로 상태 확인
   · Ctrl+C 발생 → thread_stop_event.set() → 각 루프의 _should_stop()이 True → 정상 종료

데이터 흐름(각 스레드 공통)
   sensor.set_env() / 수집함수() → MissionComputer.env_values 또는 dict → json.dumps → 콘솔
   (센서 로그는 DummySensor.get_env(log=True) 경로로 파일에 남김)
```

## 2) 멀티프로세스 구성
```text
메인 프로세스
   ├─ proc 1: _run_info_process(MC1, stop_event1)
   ├─ proc 2: _run_load_process(MC2, stop_event2)
   └─ proc 3: _run_sensor_process(MC3, stop_event3)

프로세스별 종료 신호: multiprocessing.Event()
   · 메인에서 Ctrl+C → 각 event.set() → 각 하위 프로세스 루프 종료
   · join(timeout) 후 미종료 시 terminate()로 안전 강제 종료

인스턴스 분리 원칙
   · MC1/MC2/MC3 각각 독립 DummySensor를 소유 → 프로세스 간 상태 공유 없음
```

## 공통 레이어 도식(요약)
```text
[Random/OS/psutil] → (수집) → MissionComputer/DummySensor → (가공) → dict → json.dumps → 콘솔
                                        └─(옵션) DummySensor._log_env → mission_env.log
[Event] ──────→ _should_stop() → while 루프 탈출
```

레전드
- 사각형: 객체/컴포넌트(클래스/프로세스/스레드)
- 화살표: 데이터/제어 흐름 방향
- 대괄호[]: 외부 의존(표준 라이브러리/OS/psutil)

---

## 학습 가이드 (초보자용)

### 핵심 개념 정리
- 멀티쓰레드: 하나의 프로세스 안에서 여러 작업을 동시 진행. I/O 대기 겹치기에 유리.
- 멀티프로세스: 프로세스를 여러 개 띄워 CPU 코어를 병렬 활용. 파이썬 GIL의 제약을 회피.
- 이벤트 기반 종료: `threading.Event`/`multiprocessing.Event`로 안전하게 중지 신호 전달.

### 모듈과 import 설명
- `threading`: `Thread`, `Event`로 쓰레드와 신호 관리.
- `multiprocessing`: `Process`, `Event`, `freeze_support`(Windows) 등 멀티프로세스 지원.
- 기타 모듈은 이전과 동일.

### 함수/흐름 설명과 사례
- 스레드 3종 동시 실행:
  - A: `get_sensor_data(5s)`
  - B: `get_mission_computer_info(20s)`
  - C: `get_mission_computer_load(20s)`
  - 공용 `thread_stop_event`로 모두 종료.
- 프로세스 3종 동시 실행:
  - `_run_info_process(MC1, ev1)`, `_run_load_process(MC2, ev2)`, `_run_sensor_process(MC3, ev3)`
  - 각 프로세스에 별도 `Event`를 전달해 종료.

사례(흐름)
```python
thread_stop_event = threading.Event()
threads = [
  threading.Thread(target=mc.get_sensor_data, kwargs={'interval_sec':5,'stop_event':thread_stop_event}),
  threading.Thread(target=mc.get_mission_computer_info, kwargs={'interval_sec':20,'stop_event':thread_stop_event}),
  threading.Thread(target=mc.get_mission_computer_load, kwargs={'interval_sec':20,'stop_event':thread_stop_event}),
]
for t in threads: t.start()
# Ctrl+C → thread_stop_event.set() → 각 루프가 정상 종료
for t in threads: t.join()
```

### 문법/운영 가이드
- Windows에서는 `if __name__ == '__main__':` 가드와 `freeze_support()`를 반드시 사용.
- `join(timeout)` 후 살아 있으면 `terminate()`로 안전 종료(좀비/대기 방지).
- 데몬 스레드보다 명시적 종료 신호(Event)와 `join()` 사용을 권장.

### 타입 힌트
- 프로세스/스레드 대상 함수 인자의 타입을 명확히 적으면 런칭 코드에서 실수를 줄임.
- `object | None` 같은 유니언 타이핑으로 이벤트가 선택적임을 표현.

### 추가 팁
- 로그/출력량이 많을수록 동시성 환경에서 간섭(섞여 보임) 가능 → 필요 시 파일/큐 사용.
- CPU 바운드 작업은 멀티프로세스, I/O 바운드는 멀티쓰레드가 적합한 경우가 많음.

## 보너스 기능(문제 4)
- 멀티쓰레드/멀티프로세스 중 `q` 키 입력으로 중간 정지 가능.
  - 메인 프로세스의 키보드 모니터 스레드가 `q`를 감지하면, 쓰레드용 Event/프로세스용 Event를 모두 set 하여 안전 종료합니다.
- Ctrl+C도 동일하게 안전 종료 경로로 처리합니다.

### 참고: 타입 별칭(MPEvent)
- 정적분석(Pylance) 경고를 피하고 의미를 분명히 하기 위해, 보조 프로세스 함수의 이벤트 타입을 별칭으로 표기했습니다.
  - `from multiprocessing.synchronize import Event as MPEvent`
  - `_run_*_process(..., stop_event: MPEvent)`
- 이유: `multiprocessing.Event`는 팩토리 함수이고, 실제 타입은 `multiprocessing.synchronize.Event`라서 타입 자리에서 혼동이 생길 수 있기 때문입니다.

## Troubleshooting / Notes
- 키 중단(Windows 전용): `q` 키 감지는 `msvcrt` 의존. 비Windows 환경은 Ctrl+C 사용.
- 타입 별칭: 보조 프로세스 함수 인자의 이벤트 타입은 `MPEvent` 별칭을 사용합니다. 정적 분석기 호환용(`TYPE_CHECKING` 기반)입니다.

### 입력 스레드 종료(크로스플랫폼)
- 별도 스레드에서 input()을 기다리다 키워드 일치 시 종료 이벤트를 set.
- 사용: 각 루프 함수에서 stop_word='quit' 옵션 제공.
- Windows의 msvcrt 방식(q)과 병행 가능하며, 둘 중 하나가 먼저 트리거되면 중단됩니다.
