"""Actual CMP engine result -> EngineStepResult adapter tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_OP_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from VectorSpace_Engine import (  # noqa: E402
    EngineStepResult,
    from_convergence_dynamics,
    from_semiconductor_observation,
    from_terraforming_plan,
    from_vector_calculus,
    from_wave_snapshot,
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_convergence_dynamics_adapter_maps_core_metrics():
    models = _load_module(
        "cmp02_models",
        _OP_ROOT
        / "40_SPATIAL_LAYER"
        / "ConvergenceDynamics_Engine"
        / "models.py",
    )
    dynamics = models.MethodDynamics(
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
    models = _load_module(
        "cmp07_models",
        _OP_ROOT
        / "30_CORTEX_LAYER"
        / "VectorCalculus_Engine"
        / "models.py",
    )
    gradient = models.GradientResult((0.0, 0.0, 0.0), (3.0, 4.0, 0.0))
    divergence = models.DivergenceResult((0.0, 0.0, 0.0), 0.25)
    curl = models.CurlResult((0.0, 0.0, 0.0), (0.0, 0.0, 2.0))
    laplacian = models.LaplacianResult((0.0, 0.0, 0.0), -0.5)
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
    models = _load_module(
        "cmp10_models",
        _OP_ROOT
        / "40_SPATIAL_LAYER"
        / "WaveEquation_Engine"
        / "models.py",
    )
    snapshot = models.WaveSnapshot(
        t=0.2,
        x=[0.0, 0.5, 1.0],
        y=[0.0, 1.0, 0.0],
    )
    step = from_wave_snapshot(snapshot)
    assert step.engine_id == "cmp10"
    assert step.observation["wave_energy"] == snapshot.y_rms
    assert step.observation["field_intensity"] == snapshot.y_max


def test_semiconductor_observation_adapter_maps_observer_output():
    models = _load_module(
        "cmp15_models",
        _OP_ROOT
        / "40_SPATIAL_LAYER"
        / "SemiconductorPhysics_Eval_Engine"
        / "models.py",
    )
    obs = models.SemiconductorObservation(
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
    terra = _load_module(
        "cmp18_terra",
        _OP_ROOT
        / "40_SPATIAL_LAYER"
        / "planetary_intervention_engine"
        / "terra_core.py",
    )
    gap = terra.EdenGap(
        temp_gap_C=1.5,
        gpp_gap=0.2,
        hab_band_deficit=1,
        ice_band_excess=0,
        mutation_excess=0.0,
        uv_gap=0.05,
        co2_gap_pct=0.1,
        overall_gap=0.35,
    )
    plan = terra.TerraformingPlan(
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
