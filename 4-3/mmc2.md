# MMC2: MissionComputer 개요

DummySensor에서 값을 읽어 env_values에 보관하고, 주기적으로 화면에 JSON으로 출력하는 버전입니다. 아래 도식은 구성 요소와 데이터 흐름을 간단히 보여줍니다.

```text
┌──────────────────────┐         ┌──────────────────────────────┐
│      DummySensor     │         │       MissionComputer        │
│  env_values(dict)    │  data   │  env_values(dict)            │
│  set_env() ──────────┼────────►│  get_sensor_data()           │
│  get_env(log=bool)   │         │   - sensor.set_env()         │
│  _log_env()          │         │   - env ← sensor.get_env()   │
└──────────────────────┘         │   - self.env_values.update   │
                                 │   - print(json.dumps(...))   │
                                 │   - stop_event로 종료        │
                                 └──────────────────────────────┘
```

## 핵심 포인트
- MissionComputer.env_values는 “최근 센서 스냅샷”을 담습니다(`update`로 덮어씀).
- 파일 로그는 DummySensor.get_env(log=True)가 담당합니다(CSV append). MissionComputer는 화면 출력만 합니다.
- `stop_event` 신호가 설정되면 루프가 종료됩니다.

## import 모듈 설명
- `json`: 파이썬 객체를 JSON 문자열로 직렬화(또는 역직렬화).
- `os`: 경로/파일 유틸리티(여기서는 주로 DummySensor에서 사용).
- `random`: 더미 데이터(난수) 생성(DummySensor에서 사용).
- `time`: `sleep`으로 출력 주기 제어.
- `datetime`: 로그 타임스탬프 생성(DummySensor에서 사용).

## 메서드 설명과 사례
- `__init__(self, sensor: DummySensor) -> None`
  - 센서 인스턴스를 받아 MissionComputer와 연결합니다.
  - env_values 키들을 미리 선언해 둡니다.

- `get_sensor_data(self, *, interval_sec: int = 5, log_sensor: bool = True, stop_event: object | None = None) -> None`
  - 역할: `interval_sec` 간격으로 센서 값을 가져와 `self.env_values`에 반영하고, JSON으로 출력.
  - `log_sensor=True`면 센서 쪽에서 파일 로그를 남깁니다.
  - `stop_event`가 설정되면 루프를 멈춥니다.
  - 예시:
    ```python
    run = MissionComputer(DummySensor())
    run.get_sensor_data(interval_sec=5, log_sensor=True)  # 5초마다 출력
    ```

- `@staticmethod _should_stop(flag: object | None) -> bool`
  - `flag`가 있고 `is_set()` 가능하며 True면 중지합니다.
  - 키워드 전용 인자, 유니언 타입(`object | None`)의 의미를 함께 보여줍니다.

## 문법 포인트
- 키워드 전용 인자: `*, log_sensor=...` 뒤의 인자는 `get_sensor_data(log_sensor=False)`처럼 이름으로만 전달.
- 유니언 타입: `object | None`은 “객체 또는 None”을 허용(PEP 604, Python 3.10+).
- 예외 처리: `try: ... except KeyboardInterrupt:`로 Ctrl+C를 잡아 우아하게 종료 메시지 출력.
- JSON 출력 옵션: `ensure_ascii=False`로 한글 깨짐 방지, `indent`로 들여쓰기 예쁘게.

## 타입 힌트
- 시그니처의 힌트는 “외부 API 계약(입력/출력 타입)”을 문서화합니다.
- 내부 지역 변수에도 힌트를 달 수 있지만, 런타임 강제는 하지 않습니다(정적 검사/IDE에 도움).
- 더 구체화 예: `dict[str, float | None]`처럼 키/값 타입을 명시.

## 실행 흐름(도식): mmc2.py 파일 실행 시

```text
[Program start]
  └─ if __name__ == '__main__':
      ├─ dummy_sensor = DummySensor()
      ├─ dummy_sensor.set_env()                 # 난수로 env_values 채움
      ├─ snapshot = dummy_sensor.get_env(log=True)
      │   └─ _log_env(...)가 mission_env.log에 헤더(1회)+데이터 한 줄 기록
      ├─ print(json.dumps(snapshot, ...))       # 콘솔에 보기 좋게 출력
      ├─ run_computer = MissionComputer(dummy_sensor)
      └─ run_computer.get_sensor_data(...)
          └─ while not _should_stop(stop_event):
              ├─ sensor.set_env()
              ├─ env = sensor.get_env(log=log_sensor)
              ├─ self.env_values.update(env)
              ├─ print(json.dumps(self.env_values, ...))
              └─ time.sleep(interval_sec)
```

## 내부 상태 vs 외부 저장 vs 반환
- 내부 상태
  - `DummySensor.env_values`: 센서가 보유한 현재 측정값(dict)
  - `MissionComputer.env_values`: 화면 출력용 “최근 스냅샷”을 보관하는 dict
- 외부 저장
  - `_log_env`가 `mission_env.log`에 CSV 누적 기록(헤더 1회 + 데이터 줄)
- 반환
  - `DummySensor.get_env(...) -> dict`: 현재 env_values(참조)를 반환
  - `MissionComputer.get_sensor_data(...) -> None`: 반복 출력(값 반환 없음)

## 복사용 요약(Plain Text)
- `get_sensor_data`: 주기적으로 센서 값을 받아 `env_values` 갱신 → JSON 출력. `stop_event`로 종료.
- `log_sensor=True`: 파일 로그는 DummySensor가 처리(CSV append).
- 키워드 전용 인자(`*`), 유니언 타입(`object | None`), KeyboardInterrupt 처리, JSON 옵션(`ensure_ascii`, `indent`).
- 실행 흐름: 센서 생성 → set_env → get_env(log) → JSON 출력 → MissionComputer 루프 → 주기 반복.

## 보너스 기능(문제 2)
- 특정 키로 중단: 실행 중 `q`를 누르면 반복 출력이 즉시 멈춥니다(Ctrl+C도 가능).
- 5분 평균 출력: 내부에 5분(300초) 구간의 히스토리를 유지하여 5분마다 각 항목의 평균값을 별도로 JSON으로 출력합니다(키: `5min_avg`).

## Troubleshooting / Notes
- 키 중단(Windows 전용): `q` 키 감지는 `msvcrt`를 사용하므로 Windows 콘솔에서만 동작합니다. 다른 OS에서는 Ctrl+C로 중단하세요.
- 5분 평균 확인 팁: 첫 출력은 5분이 지나야 나오므로, 테스트 시에는 코드의 300초 임계값을 임시로 줄여 확인하세요.
- 타입 경고(Pylance): `object | None`, `dict[str, ...]` 표기에서 경고가 보이면 VS Code 인터프리터를 3.10+로 바꾸거나, 본 저장소처럼 `Optional`, `Dict` 등 `typing` 표기로 바꾸면 사라집니다.

=========================================================================
## typing / Optional / Dict / Set / Deque / Tuple 정리
=========================================================================

`mmc2.py`에서 보신 `from typing import Optional, Dict, Set, Deque, Tuple`가 무엇을 가져오고 왜 쓰는지 정리합니다.

- 개요: 표준 라이브러리 `typing` 모듈은 타입 힌트(type hints)를 위한 도구를 제공합니다. 런타임 동작을 직접 바꾸는 게 아니라, 정적 타입 분석기와 IDE가 오류를 미리 잡고 자동완성을 향상시키도록 돕습니다.
- 최신 표기(Python 3.9+/3.10+):
  - 3.9+: 내장 컬렉션으로 제네릭 표기 가능: `dict[str, int]`, `set[int]`, `tuple[int, ...]` 등.
  - 3.10+: `Optional[T]` 대신 `T | None` 사용 가능.
  - 구버전 호환이나 팀 컨벤션에 따라 여전히 `typing` 별칭(`Dict`, `Set`, `Tuple`, `Deque`, `Optional`)을 쓸 수 있습니다.

=========================================================================
### typing 모듈
=========================================================================
- 정확한 명칭: 표준 라이브러리 모듈 `typing`.
- 핵심 기능: 제네릭 타입(`Dict[K, V]`, `Set[T]`), 선택 타입(`Optional[T]`), 합집합(`Union`), 리터럴(`Literal`), 프로토콜(`Protocol`), `TypedDict` 등 제공.
- 효과: mypy/pyright 같은 체커와 VS Code/PyCharm 같은 IDE가 정적 점검과 풍부한 힌트를 제공합니다.


### Optional
- 정확한 명칭: `typing.Optional[T]` (동치: `Union[T, None]`).
- 3.10+ 권장 표기: `T | None`.
- 언제 쓰나: 값이 있을 수도(None일 수도) 있을 때. 예: `def find_user(id: str) -> Optional[User]: ...`.

### Dict
- 정확한 명칭: `typing.Dict[K, V]` (내장형: `dict`).
- 3.9+ 권장 표기: `dict[K, V]`.
- 언제 쓰나: 키/값 매핑의 키와 값 타입을 명확히 할 때. 예: `env: dict[str, float | None]`.

### Set
- 정확한 명칭: `typing.Set[T]` (내장형: `set`).
- 3.9+ 권장 표기: `set[T]`.
- 언제 쓰나: 중복 없는 집합 연산이 필요할 때. 예: `visited: set[str]`.

### Deque
- 정확한 명칭: `typing.Deque[T]` (실제 클래스: `collections.deque`).
- 특징: 양쪽 끝에서 `append`, `appendleft`, `pop`, `popleft`가 평균 O(1). 큐/윈도우에 적합.
- 언제 쓰나: FIFO 큐나 좌우 양끝에서 빠른 삽입/삭제가 필요할 때. 예: `window: Deque[float]`; 생성은 `from collections import deque; d = deque([1,2,3])`.

### Tuple
- 정확한 명칭: `typing.Tuple[T1, T2, ...]` 또는 `typing.Tuple[T, ...]` (내장형: `tuple`).
- 3.9+ 권장 표기: `tuple[T1, T2]`, `tuple[T, ...]`.
- 언제 쓰나: 고정 길이(또는 가변 길이 동종)의 위치 기반 묶음을 명확히 할 때. 예: `point: tuple[int, int]`.

### 왜 대문자(캡탈) 형태인가?
- 역사적 이유: PEP 484(초기 타입 힌팅) 당시 내장 컬렉션을 제네릭으로 바로 쓸 수 없어 `Dict/Set/Tuple/Deque` 같은 대문자 별칭을 `typing`에 제공했습니다.
- PEP 585(3.9+) 이후: `dict[str, int]` 같은 내장 제네릭 표기가 가능해졌지만, 호환성을 위해 대문자 별칭도 계속 지원됩니다.
- 팀/환경 권장: 3.9+/3.10+라면 내장 표기(`dict[...]`, `set[...]`, `tuple[...]`, `T | None`)를 우선, 구버전 호환이 필요하면 `typing` 별칭 사용.

### mmc2.py와의 연결
- `from typing import Optional, Dict, Set, Deque, Tuple`: 타입 힌트로 각 컨테이너/옵셔널을 명시하기 위해 가져옵니다.
- `from collections import deque`: 실제 런타임에서 쓰는 양끝 큐 구현(데이터 조작용). `typing.Deque`는 타입 표기를, `collections.deque`는 실제 객체를 담당합니다.

### 요약(동치 관계)
- `Optional[T]` ↔ `T | None` (3.10+)
- `Dict[K, V]` ↔ `dict[K, V]` (3.9+)
- `Set[T]` ↔ `set[T]` (3.9+)
- `Tuple[T1, T2]` / `Tuple[T, ...]` ↔ `tuple[...]` (3.9+)
- `Deque[T]` ↔ `collections.deque[T]` (3.9+), 생성은 `deque([...])`

참고: `mmc2.py`의 `from __future__ import annotations`는 타입 힌트를 지연 평가해(문자열로 보관) 순환/전방 참조를 쉽게 하고, 최신 표기와의 호환성을 높입니다.


=========================================================================
## collections / deque / msvcrt 정리
=========================================================================

### collections 모듈
- 정확한 명칭: 표준 라이브러리 모듈 `collections`.
- 목적: 내장 컨테이너(`list`, `dict`, `set`, `tuple`)로 해결하기 어려운 성능/표현 문제를 위한 특수 컨테이너 제공.
- 주요 구성요소(요약):
  - `deque`: 양끝 큐(아래 상세).
  - `Counter`: 항목 빈도수 계산, `most_common()` 지원.
  - `defaultdict`: 기본값 팩토리로 자동 초기화되는 dict.
  - `namedtuple`: 필드명을 가진 가벼운 불변 튜플.
  - `OrderedDict`: 3.7+에서 `dict`도 입력 순서 보존하지만, `move_to_end` 등 전용 API가 필요할 때 사용.
  - `ChainMap`: 여러 매핑을 겹쳐 읽기(오버레이) 용도.
  - `UserDict`/`UserList`/`UserString`: 사용자 정의 래퍼 베이스 클래스.

### deque (from collections import deque)
- 정확한 명칭: 클래스 `collections.deque`.
- 특징: 양끝에서의 추가/삭제가 평균 O(1). 최대 길이(`maxlen`)로 고정 크기 버퍼(슬라이딩 윈도우) 구현 가능.
- 대표 메서드:
  - 삽입/삭제: `append`, `appendleft`, `pop`, `popleft`, `clear`.
  - 확장: `extend`, `extendleft`(주의: 왼쪽 확장은 입력 순서가 역순으로 쌓임).
  - 기타: `rotate(n)`, `reverse()`, `count(x)`, `copy()`.
- 리스트와의 차이: 리스트의 `pop(0)`/`insert(0, x)`는 O(n)이라 큐 용도로 비효율적. `deque`는 이러한 작업에 최적화.
- 타입 표기와의 관계:
  - 런타임 객체: `collections.deque`.
  - 타입 힌트: `typing.Deque[T]` 또는 3.9+에서는 `collections.deque[T]`도 가능.
- 가져오기 스타일:
  - `from collections import deque` → 코드에서 `deque(...)`로 간결하게 사용.
  - `import collections` → `collections.deque(...)`로 사용(네임스페이스 유지 선호 시).

### msvcrt (Windows 전용 콘솔 입력 등)
- 정확한 명칭: 표준 라이브러리 모듈 `msvcrt` (Microsoft Visual C Runtime 인터페이스).
- 플랫폼: Windows 전용. 비 Windows 환경에서는 `ImportError`가 발생합니다. `mmc2.py`는 `try/except ImportError`로 안전하게 처리.
- 목적(여기서의 사용 맥락): 콘솔에서 키 입력을 즉시(엔터 없이) 감지해 루프 중단 등 제어. `input()`은 줄 단위(엔터 필요)이고 블로킹이라 부적합.
- 대표 함수:
  - `kbhit()` : 키가 눌렸는지 대기열 확인(논블로킹). True면 읽을 키가 있음.
  - `getch()` : 1문자 읽기(바이트, echo 안 함). 필요 시 `.decode()`로 문자열 변환.
  - `getwch()` : 1문자 읽기(유니코드 문자열, echo 안 함). 한글 등 유니코드 입력 시 유리.
  - `putch/putwch`, `ungetch`, 파일 `locking`, `setmode`, `get_osfhandle` 등도 제공.
- 예시(논블로킹 종료 키 처리):
  ```python
  try:
      import msvcrt  # Windows
  except ImportError:
      msvcrt = None  # macOS/Linux 등에서는 없음

  def pressed_quit() -> bool:
      if msvcrt and msvcrt.kbhit():
          ch = msvcrt.getwch()  # 또는 msvcrt.getch().decode(errors='ignore')
          return ch.lower() == 'q'
      return False
  ```
- 크로스플랫폼 대안:
  - 단순 중단: `KeyboardInterrupt`(Ctrl+C) 처리.
  - Unix 계열: `curses`, `select` 등. 또는 스레드로 `input()`을 별도로 받아 폴링.
