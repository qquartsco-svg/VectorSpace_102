"""통합 수학 레이어 파이프라인 테스트."""

from __future__ import annotations

import sys
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

from VectorSpace_Engine import IntegratedMathPipeline, PipelineConfig, Verdict  # noqa: E402
from VectorSpace_Engine import EngineStepResult, GlobalSystemVectorV0, VectorAxisSpec


def test_integrated_pipeline_runs_and_sets_verdict():
    pipe = IntegratedMathPipeline(PipelineConfig(dim=3, dt=0.2))
    gsv = pipe.init_state((1.0, -1.0, 0.5))
    g2 = pipe.run_step(
        gsv,
        input_fields={
            "error": 0.2,
            "residual": 0.3,
            "noise": 0.1,
            "field_intensity": 0.4,
            "wave_energy": 0.3,
            "drift": 0.2,
            "graph_load": 0.2,
            "control_risk": 0.1,
        },
    )
    assert len(g2.x) == 3
    assert 0.0 <= g2.omega <= 1.0
    assert g2.verdict in (Verdict.JUST, Verdict.STABLE, Verdict.FRAGILE, Verdict.CRITICAL)
    assert "integrated_math_pipeline.omega" in g2.fields


def test_integrated_pipeline_run_engine_steps_projects_state():
    pipe = IntegratedMathPipeline(
        PipelineConfig(
            dim=3,
            dt=0.1,
            state_projection_keys=("cmp02.error", "cmp10.wave_energy", "cmp18.control_risk"),
        )
    )
    gsv = GlobalSystemVectorV0(
        x=(0.0, 0.0, 0.0),
        axes=(
            VectorAxisSpec("cmp02.error", "convergence error"),
            VectorAxisSpec("cmp10.wave_energy", "wave energy"),
            VectorAxisSpec("cmp18.control_risk", "control risk"),
        ),
    )
    g2 = pipe.run_engine_steps(
        gsv,
        (
            EngineStepResult("cmp02", {}, {}, {"omega": 0.9, "error": 0.1}),
            EngineStepResult("cmp10", {}, {}, {"omega": 0.7, "wave_energy": 0.2}),
            EngineStepResult("cmp18", {}, {}, {"omega": 0.8, "control_risk": 0.15}),
        ),
        engine_weights={"cmp02": 1.5, "cmp10": 1.0, "cmp18": 1.2},
    )
    assert g2.meta["integration_mode"] == "engine_steps"
    assert 0.0 < g2.omega <= 1.0
    assert len(g2.x) == 3
    assert g2.x != (0.0, 0.0, 0.0)
