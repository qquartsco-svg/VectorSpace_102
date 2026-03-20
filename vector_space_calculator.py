"""
VectorSpaceCalculator — GSV 병합, Ω 가중합, 명시 오일러 한 스텝.

CMP 플러그인 출력(EngineStepResult)을 GlobalSystemVectorV0에 누적할 때 사용.
외부 의존 없음 (표준 라이브러리만).
"""

from __future__ import annotations

from typing import Mapping, Sequence

from .vector_space_schema import EngineStepResult, GlobalSystemVectorV0, GraphRefV0
from .vector_space_core import VectorSpace, add, change_basis, distance, dot, norm, scale
from .linear_algebra import mat_add, matmul, matvec


class VectorSpaceCalculator:
    """
    상태공간 R^n 위 연산 + 스냅샷 병합.

    - combine_omega: 여러 엔진 Ω_i → 단일 스칼라
    - step_euler: x' = x + f(x)*dt (명시 오일러; 적분기 교체는 이후 확장)
    - merge_engine_step: EngineStepResult → fields/omega/meta 갱신
    """

    __slots__ = ("space",)

    def __init__(self, dim: int) -> None:
        self.space = VectorSpace(dim)

    def combine_omega(
        self,
        omegas: Mapping[str, float],
        weights: Mapping[str, float],
        *,
        default_weight: float = 1.0,
    ) -> float:
        """Ω = Σ w_k Ω_k / Σ w_k (가중 평균). 키가 없으면 default_weight."""
        if not omegas:
            return 1.0
        num = 0.0
        den = 0.0
        for k, o in omegas.items():
            w = float(weights.get(k, default_weight))
            num += w * float(o)
            den += w
        if den <= 0.0:
            raise ValueError("sum of weights must be > 0")
        return num / den

    def step_euler(
        self,
        x: tuple[float, ...],
        f: tuple[float, ...],
        dt: float,
    ) -> tuple[float, ...]:
        """x_{t+1} = x + f * dt"""
        self.space.assert_dim(x)
        self.space.assert_dim(f)
        return add(x, scale(dt, f))

    def step_rk4(
        self,
        x: tuple[float, ...],
        field_fn,
        dt: float,
    ) -> tuple[float, ...]:
        """고전 RK4 한 스텝.

        `field_fn(x)` 는 현재 상태에서 미분 벡터를 돌려준다.
        """
        self.space.assert_dim(x)
        k1 = tuple(field_fn(x))
        self.space.assert_dim(k1)
        x2 = add(x, scale(0.5 * dt, k1))
        k2 = tuple(field_fn(x2))
        self.space.assert_dim(k2)
        x3 = add(x, scale(0.5 * dt, k2))
        k3 = tuple(field_fn(x3))
        self.space.assert_dim(k3)
        x4 = add(x, scale(dt, k3))
        k4 = tuple(field_fn(x4))
        self.space.assert_dim(k4)
        total = tuple(
            (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]) / 6.0 for i in range(self.space.dim)
        )
        return add(x, scale(dt, total))

    def step_linear(
        self,
        x: tuple[float, ...],
        *,
        A: Sequence[Sequence[float]],
        B: Sequence[Sequence[float]] | None = None,
        u: Sequence[float] | None = None,
    ) -> tuple[float, ...]:
        """이산 선형 상태전이.

        x_{t+1} = A x_t + B u_t
        """
        self.space.assert_dim(x)
        ax = matvec(A, x)
        if B is None or u is None:
            return ax
        bu = matvec(B, u)
        self.space.assert_dim(bu)
        return add(ax, bu)

    def observe_linear(
        self,
        x: tuple[float, ...],
        *,
        C: Sequence[Sequence[float]],
        D: Sequence[Sequence[float]] | None = None,
        u: Sequence[float] | None = None,
    ) -> tuple[float, ...]:
        """선형 관측식.

        y_t = C x_t + D u_t
        """
        self.space.assert_dim(x)
        y = matvec(C, x)
        if D is None or u is None:
            return y
        du = matvec(D, u)
        if len(du) != len(y):
            raise ValueError("observation dim mismatch")
        return add(y, du)

    def compose_state_transition(
        self,
        A1: Sequence[Sequence[float]],
        A2: Sequence[Sequence[float]],
    ) -> tuple[tuple[float, ...], ...]:
        """연속 두 상태전이행렬의 합성 A = A2 @ A1."""
        return matmul(A2, A1)

    def merge_engine_step(
        self,
        gsv: GlobalSystemVectorV0,
        step: EngineStepResult,
        *,
        omega_key: str = "omega",
    ) -> GlobalSystemVectorV0:
        """
        엔진 한 스텝 결과를 스냅샷에 합친다.

        - observation[omega_key] 가 있으면 gsv.omega 에 반영(단일 엔진 덮어쓰기).
        - fields 에 engine_id 접두어로 observation 병합.
        """
        prefix = f"{step.engine_id}."
        new_fields = dict(gsv.fields)
        for k, v in step.observation.items():
            new_fields[prefix + k] = float(v)
        omega = gsv.omega
        if omega_key in step.observation:
            omega = float(step.observation[omega_key])
        hist = gsv.history_ptr
        if step.history:
            hist = step.history
        return GlobalSystemVectorV0(
            schema_version=gsv.schema_version,
            x=gsv.x,
            fields=new_fields,
            graph_ref=gsv.graph_ref,
            omega=omega,
            verdict=gsv.verdict,
            history_ptr=hist,
            meta={**gsv.meta, "last_engine": step.engine_id},
        )

    def merge_engine_steps(
        self,
        gsv: GlobalSystemVectorV0,
        steps: Sequence[EngineStepResult],
        *,
        omega_key: str = "omega",
        engine_weights: Mapping[str, float] | None = None,
        default_weight: float = 1.0,
    ) -> GlobalSystemVectorV0:
        """여러 엔진 step을 한 번에 병합한다.

        - fields/meta/history 는 순차 병합
        - `observation[omega_key]` 가 있는 엔진들만 모아 최종 `gsv.omega` 를 가중 평균
        """
        out = gsv
        omega_inputs: dict[str, float] = {}
        for step in steps:
            out = self.merge_engine_step(out, step, omega_key=omega_key)
            if omega_key in step.observation:
                omega_inputs[step.engine_id] = float(step.observation[omega_key])
        if omega_inputs:
            out = GlobalSystemVectorV0(
                schema_version=out.schema_version,
                x=out.x,
                fields=out.fields,
                graph_ref=out.graph_ref,
                omega=self.combine_omega(omega_inputs, engine_weights or {}, default_weight=default_weight),
                verdict=out.verdict,
                history_ptr=out.history_ptr,
                meta=dict(out.meta),
            )
        return out

    def project_fields_to_vector(
        self,
        fields: Mapping[str, float],
        keys: Sequence[str],
        *,
        default: float = 0.0,
    ) -> tuple[float, ...]:
        """선택한 scalar fields를 상태벡터 축 순서대로 추출한다."""
        vec = tuple(float(fields.get(k, default)) for k in keys)
        self.space.assert_dim(vec)
        return vec

    def transform_state(
        self,
        x: tuple[float, ...],
        *,
        basis_from: Sequence[Sequence[float]],
        basis_to: Sequence[Sequence[float]],
    ) -> tuple[float, ...]:
        self.space.assert_dim(x)
        out = change_basis(x, basis_from, basis_to)
        self.space.assert_dim(out)
        return out

    def project_box(
        self,
        x: Sequence[float],
        *,
        lower: Sequence[float] | None = None,
        upper: Sequence[float] | None = None,
    ) -> tuple[float, ...]:
        """box constraint projection."""
        self.space.assert_dim(x)
        lo = tuple(float(v) for v in (lower or tuple(float("-inf") for _ in range(self.space.dim))))
        hi = tuple(float(v) for v in (upper or tuple(float("inf") for _ in range(self.space.dim))))
        self.space.assert_dim(lo)
        self.space.assert_dim(hi)
        return tuple(min(max(float(xi), lo[i]), hi[i]) for i, xi in enumerate(x))

    def project_simplex(
        self,
        x: Sequence[float],
        *,
        total: float = 1.0,
    ) -> tuple[float, ...]:
        """nonnegative simplex projection with preserved sum."""
        self.space.assert_dim(x)
        vals = [max(0.0, float(v)) for v in x]
        s = sum(vals)
        if total < 0.0:
            raise ValueError("simplex total must be >= 0")
        if s <= 1e-15:
            base = total / self.space.dim
            return tuple(base for _ in range(self.space.dim))
        scale_factor = total / s
        return tuple(v * scale_factor for v in vals)

    def apply_constraints(
        self,
        x: Sequence[float],
        *,
        box_lower: Sequence[float] | None = None,
        box_upper: Sequence[float] | None = None,
        simplex_total: float | None = None,
    ) -> tuple[float, ...]:
        """공통 constraint projection 합성.

        1. box projection
        2. optional simplex projection
        """
        out = self.project_box(x, lower=box_lower, upper=box_upper)
        if simplex_total is not None:
            out = self.project_simplex(out, total=simplex_total)
        return out

    def with_state(
        self,
        gsv: GlobalSystemVectorV0,
        x: tuple[float, ...],
        *,
        meta_updates: Mapping[str, object] | None = None,
    ) -> GlobalSystemVectorV0:
        self.space.assert_dim(x)
        return GlobalSystemVectorV0(
            schema_version=gsv.schema_version,
            x=x,
            fields=gsv.fields,
            graph_ref=gsv.graph_ref,
            omega=gsv.omega,
            verdict=gsv.verdict,
            history_ptr=gsv.history_ptr,
            meta={**gsv.meta, **dict(meta_updates or {})},
        )

    def set_graph_ref(self, gsv: GlobalSystemVectorV0, ref: GraphRefV0) -> GlobalSystemVectorV0:
        return GlobalSystemVectorV0(
            schema_version=gsv.schema_version,
            x=gsv.x,
            fields=gsv.fields,
            graph_ref=ref,
            omega=gsv.omega,
            verdict=gsv.verdict,
            history_ptr=gsv.history_ptr,
            meta=dict(gsv.meta),
            axes=gsv.axes,
        )
