"""Canonical EngineStepResult adapters for selected CMP engines.

이 모듈은 개별 엔진의 풍부한 결과 객체를
VectorSpace_Engine 의 표준 `EngineStepResult` 로 변환한다.
"""

from __future__ import annotations

from .vector_space_schema import EngineStepResult


def from_convergence_dynamics(dynamics) -> EngineStepResult:
    return EngineStepResult(
        engine_id="cmp02",
        state={
            "steps": float(dynamics.steps),
            "final_error": float(dynamics.final_error),
        },
        derived={
            "convergence_order": float(dynamics.convergence_order),
            "lyapunov_exponent": float(dynamics.lyapunov_exponent),
            "efficiency_bits_per_iter": float(dynamics.efficiency_bits_per_iter),
        },
        observation={
            "omega": _stability_to_omega(dynamics.stability),
            "error": float(dynamics.final_error),
            "lambda": float(dynamics.lyapunov_exponent),
            "order": float(dynamics.convergence_order),
            "efficiency_bits_per_iter": float(dynamics.efficiency_bits_per_iter),
        },
        history=(),
    )


def from_vector_calculus(
    *,
    gradient=None,
    divergence=None,
    curl=None,
    laplacian=None,
) -> EngineStepResult:
    grad_mag = float(getattr(gradient, "magnitude", 0.0) or 0.0)
    div_val = float(getattr(divergence, "value", 0.0) or 0.0)
    curl_mag = float(getattr(curl, "magnitude", 0.0) or 0.0)
    lap_val = float(getattr(laplacian, "value", 0.0) or 0.0)
    field_intensity = grad_mag + abs(lap_val)
    graph_load = abs(div_val)
    drift = curl_mag
    omega = 1.0 / (1.0 + field_intensity + graph_load + drift)
    return EngineStepResult(
        engine_id="cmp07",
        state={},
        derived={
            "gradient_magnitude": grad_mag,
            "curl_magnitude": curl_mag,
        },
        observation={
            "omega": omega,
            "field_intensity": field_intensity,
            "graph_load": graph_load,
            "drift": drift,
            "divergence": div_val,
            "laplacian": lap_val,
        },
    )


def from_wave_snapshot(snapshot) -> EngineStepResult:
    return EngineStepResult(
        engine_id="cmp10",
        state={
            "t": float(snapshot.t),
        },
        derived={
            "y_max": float(snapshot.y_max),
            "y_rms": float(snapshot.y_rms),
        },
        observation={
            "omega": 1.0 / (1.0 + float(snapshot.y_rms)),
            "wave_energy": float(snapshot.y_rms),
            "field_intensity": float(snapshot.y_max),
        },
    )


def from_semiconductor_observation(observation) -> EngineStepResult:
    return EngineStepResult(
        engine_id="cmp15",
        state={},
        derived={
            "poisson_residual": float(observation.poisson_residual),
            "entropy_proxy": float(observation.entropy_proxy),
        },
        observation={
            "omega": float(observation.Omega_global),
            "drift": float(observation.current_rms),
            "field_intensity": float(observation.poisson_residual),
            "noise": float(observation.entropy_proxy),
        },
    )


def from_terraforming_plan(plan) -> EngineStepResult:
    overall_gap = float(plan.eden_gap.overall_gap)
    feasibility = float(plan.overall_feasibility)
    return EngineStepResult(
        engine_id="cmp18",
        state={
            "total_duration_yr": float(plan.total_duration_yr),
            "n_interventions": float(len(plan.interventions)),
        },
        derived={
            "overall_feasibility": feasibility,
            "overall_gap": overall_gap,
        },
        observation={
            "omega": feasibility,
            "control_risk": overall_gap,
            "graph_load": max(0.0, 1.0 - feasibility),
        },
    )


def _stability_to_omega(stability: str) -> float:
    table = {
        "SUPERLINEAR": 0.95,
        "LINEAR": 0.75,
        "SUBLINEAR": 0.45,
        "DIVERGING": 0.10,
    }
    return table.get(str(stability).upper(), 0.50)
