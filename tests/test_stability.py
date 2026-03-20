"""VectorSpace_Engine 안정성 해석 테스트."""

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

from VectorSpace_Engine import (  # noqa: E402
    StabilityClass,
    analyze_local_stability,
    dominant_eigen_abs_power,
    numerical_jacobian,
)


def test_numerical_jacobian_linear_field():
    a = ((0.8, 0.0), (0.0, 0.5))

    def field(x):
        return (
            a[0][0] * x[0] + a[0][1] * x[1],
            a[1][0] * x[0] + a[1][1] * x[1],
        )

    j = numerical_jacobian(field, (1.0, -2.0))
    assert abs(j[0][0] - 0.8) < 1e-6
    assert abs(j[1][1] - 0.5) < 1e-6
    assert abs(j[0][1]) < 1e-6
    assert abs(j[1][0]) < 1e-6


def test_dominant_eigen_abs_power():
    a = ((0.9, 0.0), (0.0, 0.4))
    rho = dominant_eigen_abs_power(a)
    assert abs(rho - 0.9) < 1e-4


def test_analyze_local_stability_stable():
    def field(x):
        return (0.6 * x[0], 0.8 * x[1])

    rep = analyze_local_stability(field, (0.0, 0.0))
    assert rep.classification == StabilityClass.STABLE
    assert rep.dominant_eigen_abs < 1.0


def test_analyze_local_stability_unstable():
    def field(x):
        return (1.2 * x[0], 0.9 * x[1])

    rep = analyze_local_stability(field, (0.0, 0.0))
    assert rep.classification == StabilityClass.UNSTABLE
    assert rep.dominant_eigen_abs > 1.0
