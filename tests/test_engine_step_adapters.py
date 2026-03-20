"""Actual CMP engine result -> EngineStepResult adapter tests."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    import VectorSpace_Engine as _vse  # type: ignore  # noqa: F401
except ModuleNotFoundError:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "VectorSpace_Engine",
        _ROOT / "__init__.py",
        submodule_search_locations=[str(_ROOT)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to bootstrap VectorSpace_Engine module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["VectorSpace_Engine"] = module
    spec.loader.exec_module(module)

from VectorSpace_Engine import (  # noqa: E402,F401
    EngineStepResult,
    from_convergence_dynamics,
    from_semiconductor_observation,
    from_terraforming_plan,
    from_vector_calculus,
    from_wave_snapshot,
)


@dataclass
class MethodDynamics:
    method_name: str
    steps: int
    final_error: float
    convergence_order: float
    lyapunov_exponent: float
    efficiency_bits_per_iter: float
    predicted_steps_to_target: int
    stability: str


@dataclass
class GradientResult:
    point: tuple[float, float, float]
    vector: tuple[float, float, float]

    @property
    def magnitude(self) -> float:
        x, y, z = self.vector
        return float((x * x + y * y + z * z) ** 0.5)


@dataclass
class DivergenceResult:
    point: tuple[float, float, float]
    value: float


@dataclass
class CurlResult:
    point: tuple[float, float, float]
    vector: tuple[float, float, float]

    @property
    def magnitude(self) -> float:
        x, y, z = self.vector
        return float((x * x + y * y + z * z) ** 0.5)


@dataclass
class LaplacianResult:
    point: tuple[float, float, float]
    value: float


@dataclass
class WaveSnapshot:
    t: float
    x: list[float]
    y: list[float]

    @property
    def y_max(self) -> float:
        return max(abs(v) for v in self.y) if self.y else 0.0

    @property
    def y_rms(self) -> float:
        if not self.y:
            return 0.0
        return (sum(v * v for v in self.y) / len(self.y)) ** 0.5


@dataclass
class SemiconductorObservation:
    Omega_global: float
    verdict: str
    poisson_residual: float
    current_rms: float
    entropy_proxy: float
    stage: str


@dataclass
class EdenGap:
    temp_gap_C: float
    gpp_gap: float
    hab_band_deficit: int
    ice_band_excess: int
    mutation_excess: float
    uv_gap: float
    co2_gap_pct: float
    overall_gap: float


@dataclass
class TerraformingPlan:
    eden_gap: EdenGap
    interventions: tuple[object, ...]
    phases: tuple[object, ...]
    domain_feasibility: dict[str, float]
    overall_feasibility: float
    feasibility_label: str
    total_duration_yr: int
    summary: str


def test_convergence_dynamics_adapter_maps_core_metrics():
    dynamics = MethodDynamics(
        method_name="newton",
        steps=8,
        final_error=1e-4,
        convergence_order=2.0,
        lyapunov_exponent=-0.5,
        efficiency_bits_per_iter=3.2,
        predicted_steps_to_target=12,
        stability="SUPERLINEAR",
    )
    step = from_convergence_dynamics(dynamics)
    assert isinstance(step, EngineStepResult)
    assert step.engine_id == "cmp02"
    assert step.observation["omega"] == 0.95
    assert step.observation["error"] == dynamics.final_error


def test_vector_calculus_adapter_aggregates_field_metrics():
    gradient = GradientResult((0.0, 0.0, 0.0), (3.0, 4.0, 0.0))
    divergence = DivergenceResult((0.0, 0.0, 0.0), 0.25)
    curl = CurlResult((0.0, 0.0, 0.0), (0.0, 0.0, 2.0))
    laplacian = LaplacianResult((0.0, 0.0, 0.0), -0.5)
    step = from_vector_calculus(
        gradient=gradient,
        divergence=divergence,
        curl=curl,
        laplacian=laplacian,
    )
    assert step.engine_id == "cmp07"
    assert step.observation["field_intensity"] > 0.0
    assert step.observation["graph_load"] == 0.25
    assert step.observation["drift"] == 2.0


def test_wave_snapshot_adapter_maps_energy_and_field_intensity():
    snapshot = WaveSnapshot(
        t=0.2,
        x=[0.0, 0.5, 1.0],
        y=[0.0, 1.0, 0.0],
    )
    step = from_wave_snapshot(snapshot)
    assert step.engine_id == "cmp10"
    assert step.observation["wave_energy"] == snapshot.y_rms
    assert step.observation["field_intensity"] == snapshot.y_max


def test_semiconductor_observation_adapter_maps_observer_output():
    obs = SemiconductorObservation(
        Omega_global=0.73,
        verdict="STABLE",
        poisson_residual=0.15,
        current_rms=0.25,
        entropy_proxy=0.05,
        stage="STABLE",
    )
    step = from_semiconductor_observation(obs)
    assert step.engine_id == "cmp15"
    assert step.observation["omega"] == 0.73
    assert step.observation["drift"] == 0.25


def test_terraforming_plan_adapter_maps_control_risk():
    gap = EdenGap(
        temp_gap_C=1.5,
        gpp_gap=0.2,
        hab_band_deficit=1,
        ice_band_excess=0,
        mutation_excess=0.0,
        uv_gap=0.05,
        co2_gap_pct=0.1,
        overall_gap=0.35,
    )
    plan = TerraformingPlan(
        eden_gap=gap,
        interventions=(),
        phases=(),
        domain_feasibility={"atmosphere_risk": 0.8},
        overall_feasibility=0.72,
        feasibility_label="high",
        total_duration_yr=120,
        summary="test plan",
    )
    step = from_terraforming_plan(plan)
    assert step.engine_id == "cmp18"
    assert step.observation["omega"] == 0.72
    assert step.observation["control_risk"] == 0.35
