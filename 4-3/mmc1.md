# MMC1: DummySensor 개요

아래 도식은 DummySensor의 내부 구성과 데이터 흐름을 간단히 설명합니다. 본문은 일반 문단/불릿으로 정리했고, 도식만 코드 블록으로 처리했습니다.

```text
┌────────────────────────────────────────────────────────────────┐
│                          DummySensor                           │
│                                                                │
│  클래스 변수: LOG_PATH = 'mission_env.log'                     │
│                                                                │
│  인스턴스 변수: env_values(dict)                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 'mars_base_internal_temperature'      -> float | None    │  │
│  │ 'mars_base_external_temperature'      -> float | None    │  │
│  │ 'mars_base_internal_humidity'         -> float | None    │  │
│  │ 'mars_base_external_illuminance'      -> float | None    │  │
│  │ 'mars_base_internal_co2'              -> float | None    │  │
│  │ 'mars_base_internal_oxygen'           -> float | None    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  메서드                                                        │
│  - set_env(): 범위 내 난수 생성 → env_values 채움              │
│  - get_env(log=True): 현재 env_values 반환, 필요 시 파일 로그  │
│  - _log_env(env): CSV 헤더(최초 1회) + 데이터 한 줄 추가       │
└────────────────────────────────────────────────────────────────┘
```

## 핵심 포인트
- env_values는 “키:값” 쌍을 담는 딕셔너리로, 센서 항목 이름(키)과 측정값(값)을 저장합니다.
- set_env는 항목별 허용 범위에서 난수를 만들어 env_values를 채웁니다.
- get_env는 현재 스냅샷을 돌려주고, log=True면 파일(`mission_env.log`)에 CSV 한 줄을 기록합니다.
- LOG_PATH는 클래스 변수(모든 인스턴스가 공유), env_values는 인스턴스 변수(각 인스턴스마다 독립)입니다.

## 학습 가이드(초보자용)

### 기본 개념
- 변수: 값을 담아두는 이름표. (예) `ts = '2025-01-01 12:00:00'`.
- 딕셔너리(dict): 키(key)와 값(value)을 짝으로 보관. (예) `{'temp': 21.5, 'humidity': 55.0}`.
- 클래스(class): 관련 데이터(속성)와 기능(메서드)을 묶는 설계도. `DummySensor`가 클래스입니다.
- 인스턴스(instance): 클래스로부터 만들어진 실제 객체. `sensor = DummySensor()`.
- 인스턴스 변수: `self.env_values`처럼 객체마다 독립적으로 가지는 속성.
- 클래스 변수: `LOG_PATH`처럼 모든 인스턴스가 공유하는 속성.

### import 한 모듈
- `json`: 파이썬 객체를 JSON(문자열)로 바꾸거나 그 반대. 출력 포맷을 표준화합니다.
- `os`: 파일 존재 확인(`os.path.exists`) 등 운영체제 기능 사용.
- `random`: 난수 생성(더미 데이터 만들 때 사용).
- `datetime`: 현재 시각(`datetime.now()`)과 문자열 포맷(`strftime`).

### 주요 메서드와 사용 예
- `__init__(self) -> None`: 인스턴스가 만들어질 때 한 번 실행. 센서 항목을 `env_values`에 미리 준비.
- `set_env(self) -> None`: 각 항목 범위에서 난수를 생성해 `env_values`를 갱신.
- `get_env(self, *, log: bool = True) -> dict`: 현재 `env_values`를 반환. `log=True`면 로그 파일에 기록.
- `_log_env(self, env: dict) -> None`: CSV 형태(헤더 1회 + 데이터 한 줄)로 파일에 추가 기록.

### 문법(간단 정리)
- 들여쓰기: 공백 4칸 권장(PEP 8). 같은 수준의 코드는 같은 들여쓰기를 유지.
- 작은따옴표: 문자열은 `'...'`를 기본으로 사용(요구사항).
- f-string: `f'{값}'` 형태로 문자열에 변수/표현식을 삽입.
- with 문: 파일을 안전하게 열고 자동으로 닫음. `with open(..., 'a', encoding='utf-8') as f:`
- 키워드 전용 인자: `def f(*, x=1)`에서 `x`는 반드시 `f(x=1)`처럼 이름으로 전달.

### 타입 힌트
- 매개변수: `log: bool` → `log`가 불리언(True/False)이라는 “의도”를 문서화.
- 반환: `-> dict` → 함수가 딕셔너리를 돌려준다는 의도. 런타임 강제는 아니지만 도구가 검사.
- 위치 차이: 시그니처(함수 정의 줄)의 힌트는 “외부에 공개되는 계약”, 함수 내부 변수 힌트는 “코드 읽기/도구 분석 보조”.

---
===================================================================
## round(x, 2)
===================================================================

- 의미: 소수 둘째 자리까지 남기고, 셋째 자리에서 반올림합니다.
- 동작 원리:
  - 결과에는 소수점 아래 2자리만 남습니다.
  - 셋째 자리(0.001 자리)를 보고 반올림 여부를 결정합니다.
- 예시:
  ```python
  round(1.234, 2)  # 1.23  (셋째 자리 4 → 내림)
  round(1.236, 2)  # 1.24  (셋째 자리 6 → 올림)
  round(12.0, 2)   # 12.0  (둘째 자리까지 표시)
  ```
- 주의사항(파이썬 3의 반올림 규칙):
  - `round(2.5) == 2`, `round(3.5) == 4` (은행가 반올림 + 부동소수점 영향)
  - 금융처럼 “5면 무조건 올림”이 필요하면 `decimal` 모듈 사용 권장.
  ```python
  from decimal import Decimal, ROUND_HALF_UP
  Decimal('1.235').quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)  # Decimal('1.24')
  ```
- 한줄 요약: “소수 둘째 자리까지 표시, 셋째 자리에서 반올림”.



===================================================================
## random.uniform(a, b)
===================================================================

- 의미: a와 b 사이에서 “연속(실수) 균등분포”로 무작위 실수 하나를 반환합니다.
  - 범위: `min(a, b) <= 결과 <= max(a, b)`
  - `a > b`여도 내부에서 자동 교환되어 동작합니다.
- 언제 쓰나: 더미 센서처럼 연속 실수 값(온도, 습도, 광량 등)이 필요한 경우.
- 예시:
  ```python
  import random
  x = random.uniform(18, 30)           # 18.0 이상 30.0 이하
  temp = round(random.uniform(18, 30), 2)  # 소수 둘째 자리까지 반올림
  ```
- 시드 고정(재현성):
  ```python
  random.seed(1234)
  random.uniform(0, 1)  # 실행마다 같은 순서의 난수
  ```
- 관련 함수 비교:
  - `random()` → 0.0 ≤ N < 1.0 (단위구간 실수)
  - `randint(a, b)` → a 이상 b 이하 “정수”
  - `randrange(...)` → 정수 범위에서 규칙 추출
  - `gauss(mu, sigma)`, `normalvariate(mu, sigma)` → 정규분포(가우시안)
- 주의: 부동소수점 특성상 경계값이 정확히 나오지 않을 수 있음. 보안용 난수는 `secrets` 권장.


===================================================================
## random.seed(a=None)
===================================================================

- 역할: 의사난수 생성기(PRNG)의 시작 상태(시드)를 설정합니다. 같은 시드를 쓰면 같은 난수 시퀀스를 재현할 수 있습니다.
- 언제 쓰나: 테스트/데모/문서 예제처럼 “실행할 때마다 같은 결과”가 필요할 때.
- 동작 요약:
  - `a`가 같으면 난수 시퀀스가 동일합니다(결정적). `a=None`이면 시스템 시드(시간 등)를 써서 매번 달라집니다.
  - 전역 상태를 바꾸므로 같은 프로세스 내 `random.*` 호출 전체에 영향이 있습니다.

### 예시(재현성 확인)
```python
import random

random.seed(1234)
print(round(random.uniform(18, 30), 2))  # 23.47 (예)
print(round(random.uniform(18, 30), 2))  # 22.35 (예)

random.seed(1234)
print(round(random.uniform(18, 30), 2))  # 23.47 (같은 시드 → 같은 결과)
print(round(random.uniform(18, 30), 2))  # 22.35
```

### 주의사항
- 보안용 아님: 예측 가능하므로 암호/토큰 생성엔 `secrets` 모듈을 사용하세요.
- 전역 PRNG 상태: `random.seed`는 모듈 전역 발생기의 상태를 바꿉니다. 독립 인스턴스가 필요하면 `rng = random.Random(1234)`처럼 별도 객체를 써서 `rng.uniform(...)`을 호출하세요.
- 멀티프로세스/멀티스레드: 각 프로세스마다 별도로 시딩하세요. 스레드 간에는 전역 상태 공유에 유의.

### 참고
- 시드는 정수/바이트/문자열 등 해시 가능한 값이면 됩니다.
- 결정적 결과는 파이썬/라이브러리 버전에 따라 미세 차이가 날 수 있으니, 테스트에서는 동일 환경을 권장합니다.

### 복사용 요약(Plain Text)
- `random.seed(a)`: PRNG 시드 설정 → 같은 시드면 같은 난수 시퀀스(재현성). 전역 상태를 바꾸므로 테스트/데모에서 한 번만 설정 권장.

## random.seed(1234) 그래서 뭐가 달라지나요?

- 한 줄 요약: “랜덤의 시작점을 고정”합니다. 그래서 실행할 때마다 같은 ‘랜덤’ 값 순서를 다시 얻을 수 있어요(재현성↑).
- 언제 유용할까?
  - 테스트/디버그: 어제 본 값이 오늘도 똑같이 나와야 원인을 비교할 수 있어요.
  - 문서/데모: 예제 코드 실행 결과가 매번 같아야 설명이 쉬워요.

### 바로 체감하기
- 시드 없이(실행할 때마다 다를 수 있음)
```python
import random
print(round(random.uniform(18, 30), 2))  # 실행 1: 23.47, 실행 2: 22.35 (매번 달라질 수 있음)
print(round(random.uniform(18, 30), 2))
```
- 시드 고정(실행할 때마다 동일한 순서)
```python
import random
random.seed(1234)                       # 시작점을 고정
print(round(random.uniform(18, 30), 2))  # 실행 1: 23.47, 실행 2: 23.47 (같은 순서 보장)
print(round(random.uniform(18, 30), 2))  # 실행 1: 22.35, 실행 2: 22.35
```
- 같은 시드를 다시 주면 같은 순서가 ‘다시’ 시작됩니다
```python
import random
random.seed(1234)
print(round(random.uniform(18, 30), 2))  # 1번째 값
print(round(random.uniform(18, 30), 2))  # 2번째 값

random.seed(1234)                        # 같은 시드로 리셋
print(round(random.uniform(18, 30), 2))  # 1번째 값과 동일
print(round(random.uniform(18, 30), 2))  # 2번째 값과 동일
```

### 꼭 기억할 3가지
- 한 번만 고정: 보통 파일 시작 부분에서 `random.seed(1234)` 한 번이면 충분합니다.
- 반복 시 주의: 루프 안에서 매번 `seed`를 부르면 값이 계속 똑같이 반복돼요(진짜 랜덤처럼 안 보임).
- 보안 목적 X: 예측 가능한 값이라 비밀번호/토큰에는 쓰면 안 됩니다(`secrets` 모듈 사용).

### 추가로
- 전역 상태를 안 바꾸고 싶다면 독립 난수기 사용
```python
import random
rng = random.Random(1234)               # 전역과 분리된 PRNG 인스턴스
print(rng.uniform(18, 30))
```
- 환경/파이썬 버전에 따라 소수점 끝자리가 아주 살짝 달라질 수 있어요. 그래도 “같은 시드 → 같은 순서” 원칙은 같습니다.


===================================================================
## _log_env 이름의 앞에 `_`가 붙는 이유
===================================================================


- 한 줄 요약: 앞에 `_`를 붙이면 “내부용(비공개로 쓰길 권장)”이라는 신호입니다. 파이썬이 강제로 막지는 않지만, 공개 API가 아니라는 뜻을 문서로 남기고, `from module import *` 시에도 기본적으로 제외됩니다.

### 언제/왜 쓰나
- 공개 API가 아닌 “도우미 메서드/함수”를 표시할 때: `_log_env`는 외부 사용자가 직접 호출하기보다, `get_env()` 안에서만 쓰라고 의도한 내부용 헬퍼이기 때문입니다.
- 모듈의 공개 범위 줄이기: 모듈 최상위에서 `_helper`처럼 만들면 `from x import *`에 포함되지 않습니다(명시적 공개를 원하면 `__all__` 사용).
- 팀 컨벤션/IDE·린터 연계: IDE에서 “internal”로 표시하거나, 린터가 외부 접근을 경고해 주는 경우가 많습니다.

### 파이썬의 네이밍 컨벤션 요약
- `_name`(단일 선행 언더스코어)
  - 의미: 내부용(약한 비공개). 강제 접근 제한은 없음.
  - 효과: `from module import *`에서 기본적으로 제외.
  - 사용: 클래스의 내부 메서드/속성, 모듈의 내부 함수/상수.
- `__name`(이중 선행 언더스코어, 끝에 언더스코어 없음)
  - 의미: “네임 맹글링(name mangling)”이 적용돼 클래스 외부에서 실수로 접근하기 어렵게 함.
  - 동작: `__secret` → 내부적으로 `_ClassName__secret`으로 바뀜.
  - 사용: 서브클래스와의 이름 충돌을 피하면서 강하게 감추고 싶을 때.
- `name_`(단일 후행 언더스코어)
  - 의미: 키워드/내장과 이름 충돌을 피할 때. 예: `class_`, `id_`.
- `__name__`(양쪽 이중 언더스코어)
  - 의미: 매직/스페셜 메서드. 예: `__init__`, `__repr__`, `__len__` 등. 사용자가 임의로 만드는 일반 이름과 구분.

### 클래스에서의 의미(실전)
```python
class Sensor:
    def public(self):            # 공개 API
        return self._helper()     # 내부 헬퍼만 호출

    def _helper(self):           # 내부용: 외부에서 직접 쓰지 않길 권장
        ...

    def __really_private(self):  # 맹글링: _Sensor__really_private 로 이름 변경됨
        ...
```
- `public()`은 문서로 안내하는 공개 메서드이고, `_helper()`는 구현을 돕는 내부 메서드입니다.
- `__really_private()`는 이름이 맹글링되어 외부에서 실수로 덮어쓰거나 호출하기 어렵습니다.

### 모듈 수준에서의 의미
```python
# module.py
_public = 1     # 내부용(관례)
useful = 2      # 공개용

def _internal():
    ...

__all__ = ['useful']  # 이 모듈의 공식 공개 목록을 명시적으로 지정
```
- `from module import *`를 하면 `useful`만 가져와지고 `_public`, `_internal`은 제외됩니다.
- `__all__`로 공개 대상을 강제할 수도 있습니다.

### _log_env에 적용
- `_log_env`는 DummySensor의 “내부 로깅 도우미”입니다.
  - 외부 사용자가 직접 호출하기보다는 `get_env(log=True)`로만 트리거되게 의도.
  - 구현을 분리해 가독성을 높이고, 공개 API 표면(public surface)을 줄이는 장점이 있습니다.
- 필요하면 문서에 “내부용”이라고 적고, 공개 API 목록(예: README/문서)의 함수 리스트에는 포함하지 않습니다.

### 접근은 가능할까?
- 가능해요. 파이썬은 언어 차원에서 막지 않습니다(“합의의 언어”). 하지만 컨벤션을 따라 내부용은 외부에서 호출하지 않는 것이 좋습니다.
- 강한 은닉이 필요하면 `__name` 맹글링을 고려할 수 있지만, 테스트/디버깅 편의성 때문에 대부분은 `_name` 관례를 선호합니다.

---
===================================================================
## datetime 정리
===================================================================


- `.now()`를 왜 쓰나요?
  - 현재(로컬) 날짜·시간을 한 번에 가져옵니다. 로그 타임스탬프를 남기거나 파일명/레코드를 구분할 때 유용합니다.
  - 예:
    ```python
    from datetime import datetime
    ts = datetime.now()  # 현재 로컬 시각
    ```
- 다른 걸 쓸 수는 없나요?
  - `datetime.utcnow()` → UTC 기준 현재 시각(타임존 정보 없음).
  - `datetime.now(timezone.utc)` → 타임존이 포함된 현재 시각(권장: 명시적 타임존).
  - `datetime.today()` → now()와 사실상 동일(로컬 시각), 의미상 today라 혼동 가능해서 now 권장.
  - `time.time()` → UNIX epoch(초, float). 수치 비교/측정엔 편하지만 사람이 읽기엔 불편.
  - 필요에 따라 선택: “사람이 보는 로그”면 now(+strftime), “측정/차이 계산”이면 time.time 또는 now() 끼리 빼기.
- `.strftime`은 무엇의 약자이며 왜 쓰나요?
  - ‘string format time’의 약자입니다. datetime 객체를 “문자열”로 바꿉니다.
  - 예:
    ```python
    from datetime import datetime
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 2025-01-01 12:34:56
    ```
  - 왜 쓰나: CSV/로그/화면 표시에 사람이 읽기 좋은 형식이 필요할 때. (대안: `datetime.isoformat()`은 ISO‑8601 표준 형식)

===================================================================
### 왜 `from datetime import datetime`을 쓰나요? (`import datetime`와 차이)
===================================================================

- 두 방식 모두 됩니다. 차이는 “이름을 어떻게 쓰느냐”와 “네임스페이스 충돌 위험”이에요.

1) `from datetime import datetime`
   - 의미: 모듈 `datetime` 안의 `datetime` 클래스를 현재 네임스페이스로 가져옴.
   - 사용: `datetime.now()` 처럼 바로 클래스 이름으로 호출할 수 있어 짧고 간결합니다.
   - 예:
     ```python
     from datetime import datetime
     ts = datetime.now()
     ```

2) `import datetime`
   - 의미: 모듈 자체를 가져옴(모듈 이름과 클래스 이름이 동일한 ‘datetime’이라 중첩 표기가 필요).
   - 사용: `datetime.datetime.now()` 처럼 모듈명.클래스명으로 써야 합니다(길지만 충돌이 덜 남).
   - 예:
     ```python
     import datetime
     ts = datetime.datetime.now()
     ```

3) 별칭 사용(충돌/가독성 타협)
   - `import datetime as dt` → `dt.datetime.now()`
   - 또는 `from datetime import datetime as DateTime` → `DateTime.now()`

- 어떤 걸 선택?
  - 짧고 자주 쓰면: `from datetime import datetime`이 편리합니다(현재 코드 스타일과 동일).
  - 이름 충돌을 확실히 피하고 싶으면: `import datetime`(또는 별칭)을 권장합니다.
  - 주의: 변수 이름을 `datetime`으로 다시 쓰면(오버라이드) 나중에 클래스를 못 쓰게 될 수 있으니 피하세요.


===================================================================
## f-string에서 `{}` 여러 개 사용 가능?
===================================================================

- 가능합니다. 한 문자열 안에 표현식을 여러 개 넣을 수 있습니다.
  ```python
  name, temp = 'BASE-A', 23.456
  line = f'{name},{temp:.2f},{datetime.now():%Y-%m-%d %H:%M:%S}'
  # 예: BASE-A,23.46,2025-01-01 12:34:56
  ```
- 서식 지정(콜론 뒤): `{값:.2f}`(소수 둘째), `{dt:%Y-%m-%d}`(날짜 서식) 등.
- 중괄호 자체를 출력하려면 `{{` 또는 `}}`로 이스케이프합니다.
===================================================================
## `mode='a'`는 무엇인가(파일 열기 모드)
===================================================================

- `'a'`(append): 파일 끝에 “추가”로 씁니다. 파일이 없으면 새로 만듭니다. 기존 내용은 보존됩니다.
- 비교
  - `'w'`: “덮어쓰기(Truncate)”—파일을 비우고 새로 씀. 없으면 생성.
  - `'x'`: 새 파일 만들기 전용—이미 있으면 예외 발생.
  - `'a+'`: 추가 + 읽기 가능(파일 포인터는 끝). 필요 시 `seek(0)`으로 처음으로 이동.
- 본 코드에서 `'a'`를 쓰는 이유: 로그를 시간 순서대로 계속 이어붙여(append) 기록하기 위해서입니다.

===================================================================
## 왜 `file_exists`를 넣었는가
===================================================================

- 목적: CSV 헤더를 “처음 한 번만” 쓰기 위해서입니다.
  - 파일이 처음 생성될 때만 `datetime, ...` 같은 헤더 라인을 기록하고, 그 이후엔 데이터 줄만 추가해야 중복 헤더가 생기지 않습니다.
- 구현 방법(여러 선택지)
  1) 지금 방식: `os.path.exists(path)`로 존재 여부를 확인 → 없으면 헤더 쓰기
  2) 파일 크기 확인: `Path(path).exists() and Path(path).stat().st_size == 0` → 빈 파일이면 헤더
  3) 열고 나서 포인터 확인: `with open(path, 'a+') as f: f.seek(0,2); empty = f.tell() == 0`
  - 어느 방식이든 “헤더는 처음 한 번만”이라는 의도를 지키면 됩니다.
- 간단 예시(대안 2):
  ```python
  from pathlib import Path
  p = Path('mission_env.log')
  need_header = (not p.exists()) or (p.stat().st_size == 0)
  with p.open('a', encoding='utf-8') as f:
      if need_header:
          f.write('datetime,temp,...\n')
      f.write('2025-01-01 12:00:00,23.4,...\n')
  ```
===================================================================
## from __future__ import annotations
===================================================================

- 역할: 타입 힌트를 “나중에 평가하도록” 미룹니다. 애너테이션이 즉시 객체로 평가되지 않고 문자열로 저장돼, 순환 참조·정의 순서 문제를 피할 수 있습니다.
- 왜 쓰나:
  - 순방 참조(Forward reference) 해결: 아직 정의되지 않은 타입 이름을 힌트에 써도 됩니다.
  - 순환 의존/임포트 비용 완화: 타입 평가를 늦춰서 import 시 불필요한 의존을 줄입니다.
  - 가독성: 문자열 따옴표로 둘러싸지 않아도 자연스러운 타입 표기를 작성할 수 있습니다.
- 예시(비교)
  ```python
  # 1) 기능 없이(즉시 평가)라면 보통 문자열로 감싸야 함
  class Node:
      def __init__(self, next: 'Node | None' = None):  # 문자열 필요
          self.next = next

  # 2) 기능을 켜면(지연 평가) 문자열이 없어도 동작
  from __future__ import annotations

  class Node:
      def __init__(self, next: Node | None = None):    # 자연스럽게 표기
          self.next = next
  ```
- 어떻게 동작하나:
  - 함수/클래스의 `.__annotations__`에 타입이 문자열로 저장됩니다.
  - 실제 객체가 필요할 때 `typing.get_type_hints()`가 필요한 평가를 수행합니다.
- 함께 보면 좋은 것
  ```python
  from typing import get_type_hints

  from __future__ import annotations

  class A:
      def f(self, x: 'A', y: int) -> 'A':
          ...

  hints = get_type_hints(A.f)
  # {'x': <class '__main__.A'>, 'y': <class 'int'>, 'return': <class '__main__.A'>}
  ```
- 주의
  - “지연 평가”는 타입 힌트에만 적용됩니다. 런타임 동작은 바뀌지 않습니다.
  - 문자열이기 때문에, 평가 시점에 필요한 심볼이 import돼 있어야 `get_type_hints()`가 성공합니다.
  - 일부 도구/라이브러리는 이 동작을 전제로 하므로, 프로젝트 전반의 일관성을 유지하세요.

===================================================================
## 타입 유니언( | )는 언제 쓰나요?
===================================================================
- 한 줄 정의: `A | B`는 “값이 A 또는 B 타입일 수 있다”는 뜻의 타입 힌트입니다. (PEP 604, Python 3.10+)
- 언제 쓰나
  - 입력으로 여러 타입을 허용할 때: 정수/실수를 모두 받는 계산 함수 등
  - 출력이 경우에 따라 달라질 때: 성공 시 `str`, 실패 시 `None` 등
  - 컨테이너 내부 원소가 섞일 수 있을 때: `list[int | float]`

### 기본 예시
```python
# 매개변수: int 또는 float를 허용
def area(x: int | float, y: int | float) -> float:
    return float(x) * float(y)

# 반환: 문자열 또는 None (Optional과 동일 의미)
from typing import Optional

def fmt(v: int | float | None) -> str:
    if v is None:
        return 'N/A'
    return f'{v:.2f}'

# 컨테이너 안에서 사용
nums: list[int | float] = [1, 2.5, 3]
```

### Optional과의 관계
- `T | None`은 `Optional[T]`와 동일합니다.
  - 예: `int | None` ≡ `Optional[int]`

### 구버전 표기(typing.Union)
- Python 3.10 미만: `Union[int, str]`를 사용해야 했습니다.
- 3.10 이상: `int | str`를 권장합니다(더 간결).

### 괄호/우선순위 팁
- 제네릭 안쪽: 그대로 사용합니다.
  - `list[int | str]`, `dict[str, int | float]`
- 제네릭 자체를 유니언할 때는 의미가 달라집니다.
  - `list[int] | list[str]` (두 “리스트 타입”의 유니언)
  - `list[int | str]` (한 리스트 안에 int와 str가 섞일 수 있음)
- `Callable` 인자처럼 중첩될 때도 그대로 쓸 수 있습니다.
  - `Callable[[int | str], None]`

### 런타임과의 차이(중요)
- `int | str`는 “타입 힌트” 문법입니다. 런타임 검사에는 `isinstance(x, (int, str))`를 쓰세요.
- `int | str` 자체를 `isinstance`에 넘기면 안 됩니다.

### 언제 쓰지 말까?
- “둘 다 동시에 필요”한 구조라면 유니언이 아니라 별도 타입(튜플/데이터클래스)을 설계하세요.
  - 예: `(width: int, height: int)`가 항상 함께 있어야 하면 `tuple[int, int]` 또는 클래스로 명확히 표현.

### 요약
- `A | B`는 “A 또는 B”를 허용하는 타입 선언.
- `T | None`는 `Optional[T]`와 같다.
- 3.10+에서는 `|` 표기를 권장하고, 런타임 체크는 `isinstance(x, (A, B))`로 하세요.

---
===================================================================
## 함수 시그니처의 타입힌트와 기본값: `def get_env(self, *, log: bool = True) -> dict`
===================================================================

- `*`(키워드 전용): `*` 뒤의 매개변수는 반드시 이름으로만 전달해야 합니다.
  - 예: `get_env(log=True)`는 OK, `get_env(True)`는 TypeError.
- `log: bool = True`(기본값)
  - 의미: `log`가 전달되지 않으면 기본값 `True`가 쓰입니다.
  - 기본값은 “함수가 정의될 때 한 번” 평가되어 보관됩니다. 불변값(True/False/숫자/문자열/튜플)은 안전합니다.
  - 가변값(list/dict/set 등)을 기본값으로 쓰지 말 것. 패턴: `param: dict | None = None` → 함수 안에서 `if param is None: param = {}`.
- `-> dict`(반환 타입 힌트)
  - 의미: 이 함수가 딕셔너리를 반환하도록 “의도”했음을 문서화합니다. 런타임에서 자동 강제/변환은 하지 않습니다.
  - 더 구체화 가능: `dict[str, float | None]`처럼 키/값 타입을 명시.
- 타입힌트를 왜 쓰나
  - IDE 자동완성/정적 검사(mypy, pyright)/리팩터링/문서화에 도움. 팀/미래의 내가 코드 의도를 빠르게 이해.
  - 런타임 강제는 아님(검사는 도구가 함). “잘못된 타입을 넣으면” 실행은 될 수 있으나 경고/오류를 정적 검사에서 잡습니다.

### 함수 내부의 타입힌트(지역 변수 애너테이션)
- 형태: `x: int = 0` 또는 `x: int` (값 미지정)
  - `x: int = 0`: 값은 0으로 “대입”되고, `int`는 문서(힌트)일 뿐 실행 결과를 바꾸지 않습니다.
  - `x: int`만 있으면 기본값은 없습니다. 이후에 반드시 대입해야 합니다(안 하면 UnboundLocalError).
- 예시
  ```python
  def f() -> None:
      cnt: int = 0          # 기본값 0 대입 + 타입 의도는 int
      avg: float           # 아직 값 없음(주석적 의미), 나중에 반드시 대입
      data: dict[str, int] = {}
      # ... 로직에서 data, cnt 갱신
  ```
- 요약
  - “시그니처의 타입힌트/기본값”은 함수 입출력을 문서화하고 기본 동작을 정의.
  - “함수 내부의 타입힌트”는 변수 의도를 밝히는 주석과 같고, 기본값은 ‘대입한 값’이 전부입니다.

### 호출 예시
```python
env = sensor.get_env()              # log 기본값(True) 사용 → 파일 로그 남김
env = sensor.get_env(log=False)     # 키워드 인자로 끄기
```
===================================================================
## 왜 `self._log_env(self.env_values)` 처럼 인자를 넘기나요?
===================================================================

- 시그니처가 `def _log_env(self, env: dict) -> None`이므로, “무엇을 기록할지”를 명확히 인자로 전달하는 방식입니다.
  - 호출부: `self._log_env(self.env_values)` → 현재 환경 스냅샷을 기록하라.
- 장점(왜 굳이 넘기나?)
  1) 명시성/의존성 주입: 함수가 어떤 데이터에 의존하는지 호출부에서 드러납니다(숨은 전역/상태 의존 ↓).
  2) 재사용성: 내부 상태 말고도 임의의 딕셔너리도 기록 가능. 예: 가공한 값, 다른 센서 값 등.
  3) 테스트 용이: 단위 테스트에서 더미 dict를 넣어 바로 검증할 수 있음.
  4) 스냅샷 의미 강화: “그 시점에 기록하고 싶은 값”을 인자로 고정해서 전달.
     - 필요하면 복사본으로 더욱 안전하게: `self._log_env(dict(self.env_values))`.
- 대안(인자 없이 내부 상태를 읽기)
  ```python
  # 덜 명시적인 버전(가능은 함)
  def _log_env(self) -> None:
      env = self.env_values  # 내부 상태를 직접 참조
      ...
  ```
  - 장점: 호출이 짧아짐 `self._log_env()`.
  - 단점: 숨은 의존성(무엇을 쓰는지 함수 밖에서 보이지 않음), 테스트/재사용성 ↓.
- 타입 힌트 역할
  - `env: dict` 덕분에 정적 검사기가 잘못된 타입 전달을 잡아주고, IDE가 자동완성을 돕습니다.
  - 더 구체화 가능: `dict[str, float | None]`처럼 키/값 타입을 명시.

요약
- 인자로 넘기면 “어떤 값을 기록할지”를 명확히 하고, 재사용·테스트·스냅샷 관리에 유리합니다. 내부 상태를 직접 읽는 버전도 가능하지만, 의도를 드러내는 현재 방식이 유지보수에 더 안전합니다.


===================================================================
## 실행 흐름(도식): mmc1.py 파일 실행 시
===================================================================
```text
[Program start]
  └─ if __name__ == '__main__':
      ├─ sensor = DummySensor()
      │   └─ __init__():
      │       └─ self.env_values = {
      │            'mars_base_internal_temperature': None,
      │            'mars_base_external_temperature': None,
      │            'mars_base_internal_humidity': None,
      │            'mars_base_external_illuminance': None,
      │            'mars_base_internal_co2': None,
      │            'mars_base_internal_oxygen': None,
      │          }
      ├─ sensor.set_env()
      │   └─ 각 항목에 대해:
      │       └─ random.uniform(범위) → round(..., 2/4) → self.env_values['키'] = 값
      ├─ environment = sensor.get_env(log=True)
      │   ├─ (log=True) → self._log_env(self.env_values)
      │   │   ├─ ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      │   │   ├─ header = 'datetime,...'
      │   │   ├─ line   = f"{ts},..."
      │   │   ├─ file_exists = os.path.exists(LOG_PATH)
      │   │   └─ with open(LOG_PATH, mode='a', encoding='utf-8') as f:
      │   │       ├─ (처음이면) f.write(header + "\n")
      │   │       └─ f.write(line + "\n")
      │   └─ return self.env_values  # 환경 스냅샷 딕셔너리
      └─ print(json.dumps(environment, ensure_ascii=False, indent=2))
          └─ 콘솔(JSON 보기 좋게) 출력
```

### 데이터 흐름 요약
- 난수 생성: `random.uniform` → `env_values[항목]`에 저장(소수점 자리 반올림 포함)
- 파일 로그: `_log_env`가 `mission_env.log`에 (헤더 1회 + 데이터 줄) 누적 기록
- 콘솔: `print(json.dumps(environment, ...))`로 현재 스냅샷을 사람이 읽기 쉽게 출력

===================================================================
## 내부 상태 vs 외부 저장 vs 반환(요약)
===================================================================
- 내부 상태(in-memory)
  - `DummySensor.env_values`(인스턴스 변수, dict): 센서 항목별 현재값이 여기에 저장됩니다.
  - `set_env()`는 `random.uniform` → `round`로 값을 만들어 `env_values['키'] = 값`으로 갱신합니다.
  - `_log_env` 내부의 `ts/header/line`은 “지역 변수”로, 파일에 쓰고 함수가 끝나면 사라집니다.
  - `LOG_PATH`(클래스 변수): 로그 파일 경로를 모든 인스턴스가 공유합니다.

- 외부 저장(persistent)
  - `mission_env.log`(CSV): `_log_env`가 헤더(최초 1회) + 데이터 한 줄을 append 모드로 누적 기록합니다.
  - 파일은 프로그램이 끝나도 남으므로 이후 실행에서 이어서 확인/분석할 수 있습니다.

- 반환(return)
  - `get_env(log=True) -> dict`: 현재 `env_values` 딕셔너리를 반환합니다(기본적으로 “같은 객체” 참조).
  - `set_env() -> None`, `_log_env(...) -> None`: 값 반환 없음(부수효과: 상태 갱신/파일 기록).
  - `mmc1.py`의 `environment = sensor.get_env(log=True)`는 그 시점의 `env_values`를 참조해 `print`로 JSON 출력합니다.

### 스냅샷 vs 참조(중요)
- 현재 구현은 “참조”를 반환합니다. 즉, `environment`와 `sensor.env_values`가 같은 dict를 가리킵니다.
  - 곧바로 출력하면 문제 없지만, 이후에 `set_env()`를 또 호출하면 `environment` 내용도 함께 바뀌어 보일 수 있습니다.
- 변경에 영향받지 않는 “스냅샷”이 필요하면 “복사본”을 반환/사용하세요.
  - 호출부에서: `snapshot = dict(sensor.get_env())`
  - 함수에서(선택적): `return dict(self.env_values)`로 복사본 반환

### 함수별 입출력 요약
- `__init__`: `env_values` 키들만 `None`으로 초기화(내부 상태 지정), 반환 없음.
- `set_env`: 내부 상태(`env_values`) 갱신, 반환 없음.
- `get_env(log=True)`: (옵션) 파일 기록 후 현재 `env_values`를 반환.
- `_log_env(env)`: 인자로 받은 dict를 CSV 한 줄로 기록, 반환 없음.

===================================================================
## 왜 `self.LOG_PATH`라고 썼나요?
===================================================================

- self는 메서드를 호출한 "인스턴스"입니다. 메서드 안에서 클래스 변수에 접근하려면 보통
  self.LOG_PATH 또는 DummySensor.LOG_PATH 처럼 "속성 접근"을 해야함.
- 메서드 본문에서 그냥 LOG_PATH라고만 쓰면, "지역/전역 변수"로만 찾고 "클래스 속성"은 자동으로 찾지 않음.
  그래서 self 나 클래스명 을 붙여야함.
- self.LOG_PATH 동작순서:
  1) 인스턴스 속성에 LOG_PATH 가 있으면 그 값 사용
  2) 없으면 클래스 변수 DummySensor.LOG_PATH 사용

- LOG_PATH는 클래스 변수입니다(클래스 본문에 정의). 인스턴스에서도 `self.LOG_PATH`로 접근할 수 있습니다.
- 속성 탐색 규칙(중요):
  1) 먼저 인스턴스 사전에 같은 이름이 있으면 그 값을 사용
  2) 없으면 클래스 변수(및 상속 계층)를 찾아 사용
- 그래서 `self.LOG_PATH`를 쓰면
  - 기본적으로는 클래스 변수 값을 쓰고,
  - 필요하면 특정 인스턴스에서 `self.LOG_PATH = 'other.log'`로 “인스턴스 전용 경로”를 오버라이드할 수 있습니다.
- 대안 표기
  - `DummySensor.LOG_PATH`: 항상 클래스 변수만 가리킵니다(인스턴스 오버라이드 무시).
  - `type(self).LOG_PATH`: 현재 인스턴스의 실제 클래스에 정의된 값을 가리킵니다.
- 선택 가이드
  - 인스턴스마다 경로를 다르게 쓰고 싶을 가능성이 있다 → `self.LOG_PATH`
  - 전역적으로 하나의 경로만 써야 한다(오버라이드 방지) → `DummySensor.LOG_PATH`

- os.path.exists
  os.path.exists(path)는 str | byes | os.PathLike 를 받음. 즉 'mission_env.log' 같은 문자열을
  "경로"로 보고, 실제 파일/디렉터리가 존재하면 True, 없으면 False를 반환함

===================================================================
## `print(json.dumps(...))`는 파일에도 저장하나요?
===================================================================

- 아닙니다. `json.dumps(obj, ...)`는 “obj를 JSON 문자열로 만들어 반환”만 합니다.
  - `print(...)`는 그 문자열을 “콘솔(표준출력)에 출력”할 뿐, 파일에는 저장하지 않습니다.
- 파일에 JSON을 저장하려면:
  1) `json.dump(obj, file, ...)`로 직접 파일에 쓰기
     ```python
     import json
     with open('data.json', 'w', encoding='utf-8') as f:
         json.dump(obj, f, ensure_ascii=False, indent=2)
     ```
  2) 또는 `json.dumps(...)`로 문자열을 만든 뒤 `f.write(...)`
     ```python
     s = json.dumps(obj, ensure_ascii=False, indent=2)
     with open('data.json', 'w', encoding='utf-8') as f:
         f.write(s)
     ```
- 현재 mmc1.py에서는 파일 저장은 `_log_env`가 CSV로 처리하고, `print(json.dumps(...))`는 화면 출력만 담당합니다.
- 옵션 설명
  - `ensure_ascii=False`: 한글/유니코드를 이스케이프하지 않고 그대로 출력
  - `indent=2`: 보기 좋게 들여쓰기
