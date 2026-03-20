# VectorSpace_Engine

**역할**: 운영 수학 OS(Nexus/런타임)가 들고 다닐 **`GlobalSystemVectorV0`** 스키마와 **범용 선형대수 + R^n 상태공간 계산**을 제공한다.
즉, 이 엔진은 단순 벡터 유틸이 아니라 공학 계산기, 공간 계산기, 벡터공간 계산기, 우주/상태공간 runtime shell 역할을 맡는다.

## CMP와의 관계

- 본 모듈은 **독립 실행 가능한 상태 벡터 스냅샷 + 공간 계산기**다.
- 필요하면 상위 시스템(CMP/Observer/Runtime)에서 어댑터 계층으로 연결해 사용할 수 있다.

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
