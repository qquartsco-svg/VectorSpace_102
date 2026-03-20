# VectorSpace_Engine

**역할**: 운영 수학 OS(Nexus/런타임)가 들고 다닐 **`GlobalSystemVectorV0`** 스키마와 **범용 선형대수 + R^n 상태공간 계산**을 제공한다.
즉, 이 엔진은 단순 벡터 유틸이 아니라 공학 계산기, 공간 계산기, 벡터공간 계산기, 우주/상태공간 runtime shell 역할을 맡는다.

## CMP와의 관계

- 본 모듈은 **독립 실행 가능한 상태 벡터 스냅샷 + 공간 계산기**다.
- 필요하면 상위 시스템(CMP/Observer/Runtime)에서 어댑터 계층으로 연결해 사용할 수 있다.

## 왜 필요한가

`VectorSpace_Engine`은 "각 엔진이 따로 계산은 잘하지만, 그 결과를 하나의 런타임 상태공간으로 들고 다니기 어렵다"는 문제를 풀기 위해 설계되었다.

즉 이 모듈은:

- 여러 계산 엔진의 결과를 `EngineStepResult`로 표준화하고
- 그것을 `GlobalSystemVectorV0` 상태벡터/필드 맵으로 병합하고
- `omega`, `verdict`, `history_ptr`, `axes`를 통해 운영 가능한 런타임 스냅샷으로 유지한다.

그래서 이 엔진은 단순 수치 유틸보다 아래에 가깝다.

- 계산기(calculator)
- 상태공간 적분기(state-space integrator)
- 공학 런타임 shell(runtime shell)
- 다중 엔진 통합기(multi-engine integrator)

## 활용 시나리오

이 모듈은 다음과 같은 경우에 바로 쓸 수 있다.

- **공학 계산기**
  - 선형 상태전이, 제약조건 projection, 관측식 계산
- **벡터공간/선형대수 계산기**
  - 기저변환, 독립성 검사, 역행렬, 해법, 직교화
- **상태공간 계산기**
  - 여러 solver/observer 결과를 하나의 `GlobalSystemVectorV0`로 병합
- **우주/물리 runtime shell**
  - 파동, 반도체, 수렴 동역학, 제어, 그래프 엔진을 공통 벡터 상태로 통합
- **브레인/인지 시스템 substrate**
  - 상위 판단 엔진이 읽을 수 있는 공통 상태 표현을 제공
- **디지털 트윈 / 시뮬레이션 orchestration**
  - 여러 도메인 시뮬레이터의 출력을 한 스텝씩 결합해 운영 지표를 만들기 쉬움

## 독립 패키지 사용

이 폴더만 별도 레포 루트로 두면 standalone package 로 바로 배포할 수 있다.

```bash
pip install .
```

설치 후:

```python
from VectorSpace_Engine import (
    VectorSpaceCalculator,
    IntegratedMathPipeline,
    GlobalSystemVectorV0,
)
```

개발/테스트:

```bash
pip install -e ".[dev]"
pytest
```

블록체인/무결성 문서:

- `BLOCKCHAIN_INFO.md`
- `PHAM_BLOCKCHAIN_LOG.md`
- `SIGNATURE.sha256`

기여도 원칙:

- GNJz(Qquarts)는 이 레포에서 자신에게만 적용되는 자발적 기여도 상한을 **최대 6%**로 둔다.
- GNJz(Qquarts)는 그 어떤 상황에서도 자신의 기여도를 **6%를 넘기지 않는다**.
- 이 원칙은 상용화, 재배포, 파생 사용 여부와 무관하게 PHAM 문서에 고정된다.

## 핵심 개념

### 1. GlobalSystemVectorV0

이 구조체는 단순 벡터 하나가 아니라, 운영 가능한 상태공간 스냅샷이다.

- `x`
  - 실제 상태벡터 좌표
- `fields`
  - 엔진별 scalar 요약값 저장소
- `omega`
  - 종합 건강도 / 통합 품질 지표
- `verdict`
  - 상위 Observer/Runtime이 부여하는 최종 판정
- `history_ptr`
  - 외부 시계열 저장소와 연결되는 포인터
- `axes`
  - 각 축의 의미를 붙이는 메타데이터

### 2. EngineStepResult

각 개별 엔진이 낸 결과를 공통 구조로 맞춘 것이다.

- `state`
  - 엔진 내부 상태
- `derived`
  - 파생값/해석값
- `observation`
  - 통합에 직접 쓰일 관측값

이 표준 계약이 있기 때문에, 도메인이 달라도 결국 같은 상태공간으로 합쳐질 수 있다.

### 3. VectorAxisSpec

상태공간 축은 숫자만 있으면 의미를 잃는다.  
`VectorAxisSpec`은 각 축에:

- `key`
- `label`
- `unit`
- `domain`

을 부여해, 상용/공학 환경에서 축 의미를 유지하게 해준다.
## 사용 예

```python
from VectorSpace_Engine import (
    VectorSpaceCalculator,
    GlobalSystemVectorV0,
    EngineStepResult,
    Verdict,
)

calc = VectorSpaceCalculator(dim=4)
x = (1.0, 0.0, 0.0, 0.0)
f = (0.0, -0.1, 0.0, 0.0)
x1 = calc.step_euler(x, f, dt=0.1)

omega = calc.combine_omega(
    {"cmp02": 0.9, "cmp05": 0.4},
    {"cmp02": 1.0, "cmp05": 2.0},
)

gsv = GlobalSystemVectorV0(x=x1, omega=omega)
step = EngineStepResult(
    engine_id="cmp02",
    state={},
    derived={},
    observation={"omega": 0.85, "lambda": 1.2},
    verdict=None,
    history=(0.9, 0.88, 0.85),
)
gsv2 = calc.merge_engine_step(gsv, step)
```

실제 여러 엔진 step을 한 번에 모을 수도 있다.

```python
from VectorSpace_Engine import VectorSpaceCalculator, EngineStepResult, GlobalSystemVectorV0

calc = VectorSpaceCalculator(dim=3)
gsv = GlobalSystemVectorV0(x=(0.0, 0.0, 0.0), omega=1.0)
steps = (
    EngineStepResult("cmp02", {}, {}, {"omega": 0.9, "error": 0.1}),
    EngineStepResult("cmp10", {}, {}, {"omega": 0.7, "wave_energy": 0.3}),
)
gsv = calc.merge_engine_steps(gsv, steps, engine_weights={"cmp02": 1.5, "cmp10": 1.0})
```

`merge_engine_steps()`의 `omega`는 엔진별 `observation["omega"]`를 `engine_weights`로 가중 평균해 계산하며, 수치 observation 항목은 `fields`에 `engine_id.key` 형태로 누적 기록한다.

## 범용 선형대수 API

- 행렬: `shape`, `transpose`, `eye`, `mat_add`, `mat_scale`, `matmul`, `matvec`
- 행 소거: `rref`, `rank`
- 해석: `determinant`, `inverse`, `solve_linear`
- 벡터집합: `is_linearly_independent`, `basis`, `gram_schmidt`
- 좌표/기저: `change_basis`

## 상태전이 / 관측 / 제약조건

이 엔진은 이제 단순 벡터 유틸이 아니라, 제어공학식 상태공간 계산도 바로 처리한다.

- 상태전이:
  - `step_linear(x, A=..., B=..., u=...)`
  - `x_{t+1} = A x_t + B u_t`
- 관측:
  - `observe_linear(x, C=..., D=..., u=...)`
  - `y_t = C x_t + D u_t`
- 전이 합성:
  - `compose_state_transition(A1, A2)`
- 제약조건 projection:
  - `project_box()`
  - `project_simplex()`
  - `apply_constraints()`
- 기저변환:
  - `transform_state(...)`

## Jacobian / 안정성

- `numerical_jacobian(field_fn, x_eq)` : 수치 Jacobian 계산
- `dominant_eigen_abs_power(J)` : 지배 고유값 절대값 근사
- `analyze_local_stability(field_fn, x_eq)` : 로컬 선형화 + 안정성 분류
- 분류: `StabilityClass.STABLE | MARGINAL | UNSTABLE`

즉 이 엔진은 단순 계산 결과만 주는 것이 아니라,  
"이 상태공간이 안정적인가 / 불안정한가 / 경계적인가"까지 같이 읽을 수 있게 설계되어 있다.

## 불확실성 / 공분산 전파

- 예측 공분산: `covariance_predict(P, A, Q)`  (`P' = A P A^T + Q`)
- 업데이트 공분산: `covariance_update_joseph(...)`
- 신뢰구간: `confidence_band(x, P, z=1.96)`
- 상태 컨테이너: `UncertaintyState(x, p, q, r)`

## 통합 레이어 흐름 계산기

`IntegratedMathPipeline` 는 수학 레이어 흐름을 아래 순서로 압축해 1-step 판정을 만든다.

현재 `run_step()`은 CMP 구간별 점수 집계와 상태 projection 중심의 1-step 통합기이며, 모든 도메인 상태를 직접 진화시키는 full runtime dynamics는 후속 확장 대상으로 둔다.

- `01~05` 수렴 코어
- `06~12` 장/파동
- `13~15` 상태공간 동역학
- `16~17` 그래프/브리지
- `18~20` 제어/실행

이 파이프라인은 현재 "full world simulator"가 아니라,

- 여러 엔진 step을 병합하고
- 상태벡터를 projection하고
- 운영 판정을 만드는

**runtime integration shell** 로 이해하는 것이 가장 정확하다.

```python
from VectorSpace_Engine import IntegratedMathPipeline, PipelineConfig

pipe = IntegratedMathPipeline(PipelineConfig(dim=3, dt=0.1))
gsv = pipe.init_state((1.0, -0.5, 0.25))
gsv = pipe.run_step(
    gsv,
    input_fields={
        "error": 0.2,
        "residual": 0.1,
        "wave_energy": 0.3,
        "drift": 0.2,
        "graph_load": 0.1,
        "control_risk": 0.15,
    },
)
```

제어공학/공학 계산기 예시:

```python
from VectorSpace_Engine import VectorSpaceCalculator

calc = VectorSpaceCalculator(dim=2)
x0 = (1.0, 0.0)
A = ((1.0, 0.1), (0.0, 0.95))
B = ((0.0,), (0.1,))
u = (1.0,)

x1 = calc.step_linear(x0, A=A, B=B, u=u)
y1 = calc.observe_linear(x1, C=((1.0, 0.0),), D=((0.0,),), u=u)
x2 = calc.apply_constraints(x1, box_lower=(0.0, -1.0), box_upper=(2.0, 1.0))
```

실제 엔진 step 표준 출력(`EngineStepResult`)이 있으면, 요약 입력 없이 곧바로 상태공간으로 흘려 넣을 수 있다.

```python
from VectorSpace_Engine import IntegratedMathPipeline, PipelineConfig, EngineStepResult

pipe = IntegratedMathPipeline(
    PipelineConfig(
        dim=3,
        dt=0.1,
        state_projection_keys=("cmp02.error", "cmp10.wave_energy", "cmp18.control_risk"),
    )
)
gsv = pipe.init_state((0.0, 0.0, 0.0))
gsv = pipe.run_engine_steps(
    gsv,
    (
        EngineStepResult("cmp02", {}, {}, {"omega": 0.9, "error": 0.1}),
        EngineStepResult("cmp10", {}, {}, {"omega": 0.7, "wave_energy": 0.2}),
        EngineStepResult("cmp18", {}, {}, {"omega": 0.8, "control_risk": 0.15}),
    ),
)
```

## Verdict

`Verdict` 문자열의 **최종 부여**는 Observer/Runtime 층에서 하는 것을 권장한다. 수학 엔진은 `observation`·`omega` 기여만 한다.
`GlobalSystemVectorV0.verdict`는 상위 Runtime/Observer가 채우는 최종 판정 슬롯이며, `VectorSpace_Engine`은 기본적으로 이 값을 직접 확정하지 않고 전달/보조한다.

## GlobalSystemVectorV0 필드 의미

- `fields`: 엔진에서 올라온 장/보조 스칼라(예: `cmp10.wave_energy`)를 평탄화 저장하는 런타임 필드 맵.
- `meta`: 통합 모드, 누적 컨텍스트, 도메인 부가정보를 담는 확장 메타데이터 슬롯.
- `history_ptr`: 외부 시계열 저장소(로그/타임라인/리플레이 버퍼)와 연결하기 위한 포인터 슬롯.

## 확장성

이 모듈은 구조적으로 확장이 쉽다.

- 새 물리 엔진 추가
  - rich result -> `EngineStepResult` adapter만 만들면 됨
- 새 상태공간 축 추가
  - `VectorAxisSpec`과 projection key만 정의하면 됨
- 새 runtime 판정 추가
  - `omega` 조합 규칙과 verdict policy를 상위 Runtime에서 교체 가능
- 새 도메인 추가
  - 우주, 재료, 제어, 경제, 브레인 모델링 등 상태공간으로 번역 가능한 도메인은 대부분 수용 가능
- 새 불확실성 모듈 추가
  - covariance, confidence band, process noise 계층을 더 확장 가능

즉 `VectorSpace_Engine`은 특정 산업 하나에 묶인 계산기가 아니라,
**여러 도메인의 엔진들을 공통 상태공간 언어로 묶는 계산 substrate**를 지향한다.

## 확장 관점

- 공학 계산기:
  - 여러 solver/observer 출력을 `EngineStepResult`로 표준화해 병합
  - `A,B,C,D` 상태전이/관측식
- 공간 계산기:
  - `VectorSpace`, `distance`, `project_onto_direction`, `matvec`, `gram_schmidt`
  - `change_basis`, `transform_state`
- 상태공간 계산기:
  - `GlobalSystemVectorV0`
  - `merge_engine_steps()`
  - `run_engine_steps()`
  - `apply_constraints()`
- 우주/물리 runtime shell:
  - 파동, 양자, 반도체, 그래프, 제어 엔진 출력을 하나의 상태벡터로 통합
- 상용화 확장:
  - `VectorAxisSpec`으로 축 의미를 명시
  - 실제 도메인별 `EngineStepResult` adapter를 추가해 자동 배선 가능

## 상용화 관점

이 엔진이 상용 제품으로 유효한 이유는 다음과 같다.

- 외부 대형 프레임워크 없이 표준 라이브러리 중심으로 가볍다
- 설치형 패키지(`pyproject.toml`)로 바로 배포 가능하다
- 테스트가 붙어 있어 배포 전 회귀 확인이 쉽다
- 서명/무결성 문서가 있어 릴리스 provenance를 관리할 수 있다
- 단일 계산기라기보다 "계산 runtime core"라서 다른 제품에 내장하기 쉽다

즉 최종 제품 형태는 다양하다.

- 독립 Python 라이브러리
- 시뮬레이션 orchestration core
- 과학/공학 SaaS 백엔드 계산 코어
- 브레인/인지 모델링 런타임 substrate

## 실제 CMP adapter

이제 일부 핵심 엔진은 rich result 객체를 바로 `EngineStepResult`로 바꾸는 canonical adapter를 갖는다.

- `from_convergence_dynamics(...)` → CMP02
- `from_vector_calculus(...)` → CMP07
- `from_wave_snapshot(...)` → CMP10
- `from_connectome_observation(...)` → CMP16
- `from_semiconductor_observation(...)` → CMP15
- `from_terraforming_plan(...)` → CMP18

즉 현재 흐름은 이렇게 읽으면 된다.

```python
from VectorSpace_Engine import (
    IntegratedMathPipeline,
    PipelineConfig,
    GlobalSystemVectorV0,
    from_convergence_dynamics,
    from_wave_snapshot,
)

pipe = IntegratedMathPipeline(
    PipelineConfig(
        dim=2,
        state_projection_keys=("cmp02.error", "cmp10.wave_energy"),
    )
)

gsv = GlobalSystemVectorV0(x=(0.0, 0.0))
steps = (
    from_convergence_dynamics(cmp02_report),
    from_wave_snapshot(cmp10_snapshot),
)
gsv = pipe.run_engine_steps(gsv, steps)
```

이 단계부터는 `VectorSpace_Engine`이 단순 수동 입력 shell이 아니라,
실제 수학/물리 엔진 결과를 상태공간으로 받아먹는 통합기 역할을 한다.

## 버전

- `GlobalSystemVectorV0.schema_version` — 현재 기본 `"0.1"`.
- `schema_version`은 직렬화/교환 계약 버전이며, 하위 호환 여부 판단과 마이그레이션 분기 기준으로 사용한다.
- 패키지 버전 — `0.1.0`
