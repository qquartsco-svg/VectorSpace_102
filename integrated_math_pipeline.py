"""CMP 01~20 흐름을 상태벡터로 통합하는 벡터공간 계산기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .vector_space_calculator import VectorSpaceCalculator
from .vector_space_schema import EngineStepResult, GlobalSystemVectorV0, Verdict


@dataclass(frozen=True)
class PipelineConfig:
    dim: int
    dt: float = 0.1
    just_threshold: float = 0.85
    stable_threshold: float = 0.65
    fragile_threshold: float = 0.45
    state_projection_keys: tuple[str, ...] = ()


class IntegratedMathPipeline:
    """
    01~20 수학 레이어 흐름을 상태공간으로 압축해 한 스텝 계산한다.

    흐름:
    숫자(01~05) -> 장(06~12) -> 상태공간(13~15) -> 그래프(16~17) -> 제어(18~20) -> 판정
    """

    __slots__ = ("config", "calc")

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.calc = VectorSpaceCalculator(dim=config.dim)

    def init_state(self, x0: tuple[float, ...], *, fields: Mapping[str, float] | None = None) -> GlobalSystemVectorV0:
        self.calc.space.assert_dim(x0)
        return GlobalSystemVectorV0(x=x0, fields=dict(fields or {}), omega=1.0)

    def init_projected_state(
        self,
        *,
        fields: Mapping[str, float],
        state_projection_keys: Sequence[str] | None = None,
    ) -> GlobalSystemVectorV0:
        keys = tuple(state_projection_keys or self.config.state_projection_keys)
        if not keys:
            raise ValueError("state_projection_keys required for projected init")
        x0 = self.calc.project_fields_to_vector(fields, keys)
        return self.init_state(x0, fields=fields)

    def run_step(self, gsv: GlobalSystemVectorV0, *, input_fields: Mapping[str, float]) -> GlobalSystemVectorV0:
        self.calc.space.assert_dim(gsv.x)
        fields = {**gsv.fields, **{k: float(v) for k, v in input_fields.items()}}
        # 01~05: 수렴 코어 (오차 평균 기반)
        err_keys = ("error", "residual", "noise")
        errs = [abs(fields[k]) for k in err_keys if k in fields]
        conv = 1.0 / (1.0 + (sum(errs) / len(errs) if errs else 0.0))
        # 06~12: 장/파동 강도
        field_intensity = abs(fields.get("field_intensity", 0.0)) + abs(fields.get("wave_energy", 0.0))
        field_score = 1.0 / (1.0 + field_intensity)
        # 13~15: 동역학 드리프트
        drift = abs(fields.get("drift", 0.0))
        dyn_score = 1.0 / (1.0 + drift)
        # 16~17: 그래프 부하
        graph_load = abs(fields.get("graph_load", 0.0))
        graph_score = 1.0 / (1.0 + graph_load)
        # 18~20: 제어 안정도
        control_risk = abs(fields.get("control_risk", 0.0))
        control_score = 1.0 / (1.0 + control_risk)

        omegas = {
            "cmp01_05": conv,
            "cmp06_12": field_score,
            "cmp13_15": dyn_score,
            "cmp16_17": graph_score,
            "cmp18_20": control_score,
        }
        weights = {
            "cmp01_05": 1.5,
            "cmp06_12": 1.2,
            "cmp13_15": 1.2,
            "cmp16_17": 1.0,
            "cmp18_20": 1.4,
        }
        omega = self.calc.combine_omega(omegas, weights)

        # 상태 업데이트: 간단한 안정화 벡터장 f = -k*x
        k = max(0.0, 1.0 - omega)
        f = tuple(-k * xi for xi in gsv.x)
        x1 = self.calc.step_euler(gsv.x, f, dt=self.config.dt)

        step = EngineStepResult(
            engine_id="integrated_math_pipeline",
            state={"norm_x": sum(abs(xi) for xi in x1)},
            derived={"k": k},
            observation={"omega": omega, **omegas},
            history=(*(gsv.history_ptr[-19:]), omega),
        )
        out = self.calc.merge_engine_step(
            GlobalSystemVectorV0(
                schema_version=gsv.schema_version,
                x=x1,
                fields=fields,
                graph_ref=gsv.graph_ref,
                omega=gsv.omega,
                verdict=gsv.verdict,
                history_ptr=gsv.history_ptr,
                meta=dict(gsv.meta),
            ),
            step,
        )
        verdict = self._to_verdict(out.omega)
        return GlobalSystemVectorV0(
            schema_version=out.schema_version,
            x=out.x,
            fields=out.fields,
            graph_ref=out.graph_ref,
            omega=out.omega,
            verdict=verdict,
            history_ptr=out.history_ptr,
            meta=out.meta,
            axes=out.axes,
        )

    def run_engine_steps(
        self,
        gsv: GlobalSystemVectorV0,
        steps: Sequence[EngineStepResult],
        *,
        engine_weights: Mapping[str, float] | None = None,
        state_projection_keys: Sequence[str] | None = None,
        dt: float | None = None,
    ) -> GlobalSystemVectorV0:
        """실제 엔진 step 결과들을 받아 상태공간으로 통합한다.

        요약 scalar 입력을 수동으로 만드는 대신, 01~20 엔진이 내보낸
        `EngineStepResult` 묶음을 바로 병합하는 상위 runtime 경로이다.
        """
        merged = self.calc.merge_engine_steps(
            gsv,
            steps,
            engine_weights=engine_weights,
        )
        keys = tuple(state_projection_keys or self.config.state_projection_keys)
        if keys:
            x_target = self.calc.project_fields_to_vector(merged.fields, keys)
            # target vector 쪽으로 부드럽게 수렴시키는 간단한 안정화 장
            def field_fn(x: tuple[float, ...]) -> tuple[float, ...]:
                return tuple(x_target[i] - x[i] for i in range(self.config.dim))

            x1 = self.calc.step_rk4(merged.x, field_fn, dt=(dt or self.config.dt))
        else:
            x1 = merged.x

        verdict = self._to_verdict(merged.omega)
        return GlobalSystemVectorV0(
            schema_version=merged.schema_version,
            x=x1,
            fields=merged.fields,
            graph_ref=merged.graph_ref,
            omega=merged.omega,
            verdict=verdict,
            history_ptr=merged.history_ptr,
            meta={**merged.meta, "integration_mode": "engine_steps"},
            axes=merged.axes,
        )

    def _to_verdict(self, omega: float) -> Verdict:
        if omega >= self.config.just_threshold:
            return Verdict.JUST
        if omega >= self.config.stable_threshold:
            return Verdict.STABLE
        if omega >= self.config.fragile_threshold:
            return Verdict.FRAGILE
        return Verdict.CRITICAL
