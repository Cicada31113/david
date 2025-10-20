# Debug Notes: Interpreter · Pylance · Type Stubs · multiprocessing.Event

## (1) 인터프리터(Interpreter)란?
- 파이썬 코드를 실행하는 런타임입니다. 시스템 전역 파이썬 또는 가상환경(venv/conda)의 파이썬을 선택해 씁니다.
- VS Code의 좌하단 Python 표시에서 활성 인터프리터(예: Python 3.13.5)를 선택/변경할 수 있습니다.
- 인터프리터 버전에 따라 문법과 표준 라이브러리(타입 힌트 지원 범위)가 달라질 수 있습니다.

## (2) Pylance와 타입 스텁(Type Stubs)
- Pylance: VS Code용 Python 언어 서버로, 타입 검사/자동완성/정적 분석을 제공합니다.
- 타입 스텁(.pyi): 런타임 코드 대신 “타입 정보만 담은” 파일로, Pylance가 서명/반환 타입 등을 추론할 때 사용합니다.
- 스텁이 최신 파이썬/라이브러리 변경을 아직 반영하지 못했거나, 라이브러리 설계(런타임 객체 vs 타입) 차이로 인식 불일치가 날 수 있습니다.

## (3) 팩토리 함수(Factory Function)란?
- 클래스(타입)를 직접 노출하기보다, “호출 시 적절한 객체를 만들어 반환하는 함수”입니다.
- `multiprocessing.Event`는 실제로 동기화 객체를 만들어 반환하는 팩토리 함수이며, 내부 구현 타입은 `multiprocessing.synchronize.Event`입니다.

## (4) 왜 Pylance가 혼동하나요?
- 타입 힌트에는 “타입(클래스, 프로토콜, TypeAlias)”이 와야 합니다. 그러나 `multiprocessing.Event`는 **함수**입니다.
- 스텁/분석기 입장에선 `multiprocessing.Event`가 *타입처럼* 보장되지 않아서, 시그니처에 `multiprocessing.Event`를 직접 쓰면 경고가 뜰 수 있습니다.
- 즉, 런타임은 문제 없지만(팩토리가 인스턴스를 반환) 정적 타입 관점에서 “타입이 아니라 호출 가능한 함수”이므로 혼동이 생깁니다.

## (5) 지금 문제의 원인과 해결책

### 증상
- Python 3.13.5 인터프리터를 사용 중인데, Pylance가 `multiprocessing.Event` 타입 표기를 인식하지 못해 경고를 띄움.

### 원인
- `multiprocessing.Event`는 팩토리 함수. 타입 힌트에 *그 함수*를 직접 쓰면 “유효한 타입”으로 간주되지 않을 수 있음.

### 해결 옵션(권장 순)

#### 옵션 (A) 명시적 타입 별칭을 사용 (권장)
- Pylance가 인식하는 실제 타입을 별칭으로 가져와 시그니처에 쓰면 명확합니다.
```python
# 상단에 추가
try:
    from multiprocessing.synchronize import Event as MPEvent
except Exception:  # 환경에 따라 동작
    from multiprocessing import Event as MPEvent  # 폴백

# 사용 예시
def _run_info_process(mc: MissionComputer, stop_event: MPEvent) -> None:
    ...
```

#### 옵션 (B) 느슨한 타입으로 표시
- 간단하고 어디서나 동작합니다. 타입 엄격함은 줄어듭니다.
```python
from typing import Any, Optional

def _run_info_process(mc: MissionComputer, stop_event: Optional[Any]) -> None:
    ...
```

#### 옵션 (C) 문자열/지연 평가로 회피
- 이미 `from __future__ import annotations`가 있으면 문자열 타입 힌트가 지연 평가됩니다.
```python
# 문자열로 표기 (Pylance 환경에 따라 여전히 경고가 남을 수 있음)
def _run_info_process(mc: "MissionComputer", stop_event: "multiprocessing.synchronize.Event") -> None:
    ...
```

#### 옵션 (D) 도구/환경 조정
- VS Code / Pylance 업데이트 (최신 스텁 반영)
- 설정에서 타입체킹 모드 완화: `python.analysis.typeCheckingMode`: `basic`

---

## Quick Checklist
1) 지금 당장 경고 제거가 목표 → 옵션 A 적용(추천) 또는 옵션 B.
2) 팀 표준이 엄격한 타입이면 → 옵션 A.
3) 문서용/임시 프로젝트면 → 옵션 B로 간단히 처리.
4) 추가로 VS Code 인터프리터/확장 업데이트 점검.

---

## 참고: 예시 패치 (옵션 A)
```diff
+ try:
+     from multiprocessing.synchronize import Event as MPEvent
+ except Exception:
+     from multiprocessing import Event as MPEvent  # fallback

- def _run_info_process(mc: MissionComputer, stop_event: multiprocessing.Event) -> None:
+ def _run_info_process(mc: MissionComputer, stop_event: MPEvent) -> None:
    ...
```

이 문서는 편의를 위해 정적분석(Pylance) 관점에서의 원인과 선택지를 모았습니다. 런타임 동작은 기존 코드와 동일합니다.
