# MMC3: 시스템 정보/부하 수집 추가 도식화

MissionComputer에 시스템 정보와 부하 수집이 더해진 버전의 흐름입니다.

```text
┌──────────────────────────────┐
│        MissionComputer       │
│                              │
│  센서 스트림(get_sensor_data)│
│  ──────────────────────────  │
│  시스템 정보(get_mission_… ) │  → _collect_system_info()
│    · OS, Version, CPU,       │     - platform.system/version/processor
│      Core Count, Mem Total   │     - os.cpu_count, psutil or 대안 경로
│  부하 정보(get_mission_… )   │  → _collect_load_info()
│    · CPU%, Mem%              │     - psutil(cpu_percent, virtual_memory)
│                              │     - or getloadavg/추정
│  공통: interval_sec마다 JSON │
└──────────────────────────────┘
```

수집 경로 상세
- 메모리 총량(GB)
  - psutil.virtual_memory().total → 변환(GB)
  - psutil 미설치 시: os.sysconf(POSIX) 또는 Windows GlobalMemoryStatusEx 사용
- CPU/메모리 사용률
  - psutil 선호, 없으면 getloadavg 기반으로 CPU% 근사치

데이터 출력
- 세 함수 모두 json.dumps(dict, ensure_ascii=False)로 직렬화하여 콘솔 출력.
- 센서 데이터는 필요 시 DummySensor 내부 로그로 파일 기록.

종료 제어
- stop_event.is_set() → True 시 각 루프 종료(무한반복 대비 안전한 탈출 경로).

---

## 학습 가이드 (초보자용)

### 핵심 개념 정리
- 시스템 정보 수집: OS/버전/CPU/코어/메모리 총량 등 “정적” 성격의 정보.
- 시스템 부하 수집: CPU 사용률/메모리 사용률처럼 “실시간”으로 변하는 정보.

### 모듈과 import 설명
- `platform`: 운영체제, CPU 모델 등 식별 정보.
- `os`: `cpu_count`, `getloadavg`(일부 OS) 등.
- `psutil`(선택): CPU/메모리 사용률, 총 메모리 등 고수준 API 제공. 미설치 시 대체 경로 사용.
- 나머지(`json`, `time`, `datetime`)는 이전과 동일.

### 함수별 설명과 사례
- `get_mission_computer_info(interval_sec=20, stop_event=None)`: 20초마다 시스템 정보 dict를 JSON으로 출력.
- `get_mission_computer_load(interval_sec=20, stop_event=None)`: 20초마다 부하 정보 dict를 JSON으로 출력.
- `_collect_system_info() -> dict`: OS/버전/CPU/코어/메모리를 수집. `psutil` 없으면 OS별 대체.
- `_get_total_memory_gb() -> float | str`: 총 메모리(GB). 실패 시 `'unknown'`.
- `_collect_load_info() -> dict`: CPU%, MEM%. `psutil` 선호, 없으면 `getloadavg`로 근사치.

사례(흐름)
```python
mc = MissionComputer(DummySensor())
mc.get_mission_computer_info(interval_sec=20)
mc.get_mission_computer_load(interval_sec=20)
```

### 문법 가이드
- 정적 메서드: `@staticmethod`는 인스턴스 상태에 의존하지 않는 유틸 함수 정의 시 사용.
- 예외 래핑: 시스템 호출은 실패 가능 → `try/except`로 안전하게 감싸고 메시지 반환.

### 타입 힌트
- `-> dict`, `-> float | str`처럼 복수 타입을 반환할 수 있음을 명시하면 호출 측 처리 분기가 쉬워짐.
- 시그니처 vs 내부:
  - 시그니처: 외부 API 계약(입출력 타입)을 문서화.
  - 내부: 지역 변수/상수의 의도를 밝힘(예: `cores: int = os.cpu_count() or 1`).

### 추가 팁
- psutil이 설치되면 가장 정확. 설치가 어렵다면 대체 경로의 근사치를 사용.
- 긴 주기(예: 20초)는 시스템 부하를 줄이고, 로그량을 제어.

## 보너스 기능(문제 3)
- setting.txt로 출력 항목 제어: 같은 폴더의 `setting.txt`를 읽어 시스템 정보/부하 출력 필드를 필터링합니다.
  - 예시 파일 내용:
    ```text
    info=os,os_version,cpu_model,cpu_core_count,memory_total_gb
    load=cpu_usage_percent,memory_usage_percent
    ```
  - 파일이 없으면 모든 항목을 출력합니다.
- 특정 키로 중단: 실행 중 `q`를 누르면 각 루프가 즉시 멈춥니다.

## Troubleshooting / Notes
- setting.txt 위치: 실행 스크립트와 같은 폴더(지금은 `4-3/`). 다른 작업 디렉터리에서 실행하면 파일을 못 찾을 수 있습니다.
- setting.txt 핫리로드: 파일을 저장하면 다음 주기 출력(기본 20초)에 반영됩니다.
- Pylance 타입 경고: 구버전 표기 문제일 수 있으니 3.10+ 인터프리터를 선택하거나 `typing` 제네릭(`Dict`, `Set`)을 사용하세요.

### 입력 스레드 종료(크로스플랫폼)
- 별도 스레드에서 input()을 기다리다 키워드 일치 시 종료 이벤트를 set.
- 사용: get_sensor_data(..., stop_word='quit'), get_mission_computer_info(..., stop_word='quit'), get_mission_computer_load(..., stop_word='quit').
- Windows의 msvcrt 방식(q)과 병행 가능하며, 둘 중 하나가 먼저 트리거되면 중단됩니다.
