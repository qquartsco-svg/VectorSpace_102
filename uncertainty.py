"""불확실성/공분산 전파 유틸."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .linear_algebra import eye, mat_add, mat_scale, matmul, transpose

Matrix = tuple[tuple[float, ...], ...]
Vector = tuple[float, ...]


def covariance_predict(
    p: Sequence[Sequence[float]],
    *,
    a: Sequence[Sequence[float]],
    q: Sequence[Sequence[float]],
) -> Matrix:
    """선형 예측 공분산: P' = A P A^T + Q."""
    ap = matmul(a, p)
    apat = matmul(ap, transpose(a))
    return mat_add(apat, q)


def covariance_update_joseph(
    p_pred: Sequence[Sequence[float]],
    *,
    h: Sequence[Sequence[float]],
    r: Sequence[Sequence[float]],
    k: Sequence[Sequence[float]],
) -> Matrix:
    """Joseph form: P = (I-KH)P'(I-KH)^T + K R K^T."""
    n = len(p_pred)
    i = eye(n)
    kh = matmul(k, h)
    i_kh = mat_add(i, mat_scale(-1.0, kh))
    term1 = matmul(matmul(i_kh, p_pred), transpose(i_kh))
    term2 = matmul(matmul(k, r), transpose(k))
    return mat_add(term1, term2)


def confidence_band(x: Sequence[float], p: Sequence[Sequence[float]], *, z: float = 1.96) -> tuple[Vector, Vector]:
    """축별 신뢰구간: x_i ± z*sqrt(P_ii)."""
    xv = tuple(float(v) for v in x)
    pv = tuple(tuple(float(v) for v in row) for row in p)
    if len(pv) != len(xv) or any(len(row) != len(xv) for row in pv):
        raise ValueError("shape mismatch for confidence_band")
    lo = []
    hi = []
    for i, xi in enumerate(xv):
        var = max(0.0, pv[i][i])
        d = z * (var ** 0.5)
        lo.append(xi - d)
        hi.append(xi + d)
    return tuple(lo), tuple(hi)


@dataclass(frozen=True)
class UncertaintyState:
    """상태 + 공분산 + 측정노이즈/과정노이즈 묶음."""

    x: Vector
    p: Matrix
    q: Matrix
    r: Matrix
