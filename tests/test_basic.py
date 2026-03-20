"""VectorSpace_Engine 기본 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

# 패키지 부모를 path에 (로컬 실행용)
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from VectorSpace_Engine import (  # noqa: E402
    EngineStepResult,
    GlobalSystemVectorV0,
    VectorSpaceCalculator,
    change_basis,
    dot,
    norm,
)


def test_dot_norm():
    a = (1.0, 2.0, 2.0)
    assert dot(a, a) == 9.0
    assert abs(norm(a) - 3.0) < 1e-9


def test_combine_omega():
    c = VectorSpaceCalculator(dim=2)
    o = c.combine_omega({"a": 0.8, "b": 0.4}, {"a": 1.0, "b": 1.0})
    assert abs(o - 0.6) < 1e-9


def test_euler():
    c = VectorSpaceCalculator(dim=2)
    x = (1.0, 0.0)
    f = (0.0, -1.0)
    x1 = c.step_euler(x, f, dt=0.5)
    assert abs(x1[0] - 1.0) < 1e-9
    assert abs(x1[1] - (-0.5)) < 1e-9


def test_merge_engine_step():
    c = VectorSpaceCalculator(dim=1)
    gsv = GlobalSystemVectorV0(x=(0.0,), omega=1.0)
    step = EngineStepResult(
        engine_id="t",
        state={},
        derived={},
        observation={"omega": 0.3},
        verdict=None,
    )
    g2 = c.merge_engine_step(gsv, step)
    assert abs(g2.omega - 0.3) < 1e-9
    assert "t.omega" in g2.fields


def test_merge_engine_steps_weighted():
    c = VectorSpaceCalculator(dim=2)
    gsv = GlobalSystemVectorV0(x=(0.0, 0.0), omega=1.0)
    steps = (
        EngineStepResult("a", {}, {}, {"omega": 0.8, "error": 0.1}),
        EngineStepResult("b", {}, {}, {"omega": 0.4, "wave": 0.2}),
    )
    g2 = c.merge_engine_steps(gsv, steps, engine_weights={"a": 2.0, "b": 1.0})
    assert abs(g2.omega - ((0.8 * 2.0 + 0.4) / 3.0)) < 1e-9
    assert "a.error" in g2.fields
    assert "b.wave" in g2.fields


def test_linear_state_transition_and_observation():
    c = VectorSpaceCalculator(dim=2)
    x1 = c.step_linear(
        (1.0, 0.0),
        A=((1.0, 0.1), (0.0, 0.95)),
        B=((0.0,), (0.1,)),
        u=(1.0,),
    )
    assert len(x1) == 2
    y1 = c.observe_linear(
        x1,
        C=((1.0, 0.0),),
        D=((0.0,),),
        u=(1.0,),
    )
    assert len(y1) == 1
    assert abs(y1[0] - x1[0]) < 1e-9


def test_change_basis_and_transform_state():
    c = VectorSpaceCalculator(dim=2)
    std = ((1.0, 0.0), (0.0, 1.0))
    scaled = ((2.0, 0.0), (0.0, 3.0))
    x_scaled = change_basis((2.0, 3.0), scaled, std)
    assert x_scaled == (4.0, 9.0)
    x_std = c.transform_state((4.0, 9.0), basis_from=std, basis_to=scaled)
    assert abs(x_std[0] - 2.0) < 1e-9
    assert abs(x_std[1] - 3.0) < 1e-9


def test_constraint_projection_box_and_simplex():
    c = VectorSpaceCalculator(dim=3)
    x = (1.2, -0.5, 0.8)
    clipped = c.project_box(x, lower=(0.0, 0.0, 0.0), upper=(1.0, 1.0, 1.0))
    assert clipped == (1.0, 0.0, 0.8)
    simplex = c.project_simplex(clipped, total=1.0)
    assert abs(sum(simplex) - 1.0) < 1e-9
    assert all(v >= 0.0 for v in simplex)
