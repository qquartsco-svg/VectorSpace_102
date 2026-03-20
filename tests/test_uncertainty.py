"""VectorSpace_Engine 불확실성 전파 테스트."""

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
    confidence_band,
    covariance_predict,
    covariance_update_joseph,
)


def test_covariance_predict_identity():
    p = ((1.0, 0.0), (0.0, 2.0))
    a = ((1.0, 0.0), (0.0, 1.0))
    q = ((0.1, 0.0), (0.0, 0.2))
    out = covariance_predict(p, a=a, q=q)
    assert abs(out[0][0] - 1.1) < 1e-9
    assert abs(out[1][1] - 2.2) < 1e-9


def test_covariance_update_joseph_shapes():
    p_pred = ((1.0, 0.0), (0.0, 1.0))
    h = ((1.0, 0.0), (0.0, 1.0))
    r = ((0.1, 0.0), (0.0, 0.1))
    k = ((0.5, 0.0), (0.0, 0.5))
    out = covariance_update_joseph(p_pred, h=h, r=r, k=k)
    assert len(out) == 2 and len(out[0]) == 2
    assert out[0][0] >= 0.0 and out[1][1] >= 0.0


def test_confidence_band():
    x = (10.0, -2.0)
    p = ((4.0, 0.0), (0.0, 1.0))
    lo, hi = confidence_band(x, p, z=2.0)
    assert abs(lo[0] - 6.0) < 1e-9
    assert abs(hi[0] - 14.0) < 1e-9
    assert abs(lo[1] - (-4.0)) < 1e-9
    assert abs(hi[1] - 0.0) < 1e-9
