"""수치 Jacobian + 로컬 안정성 분류 유틸."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Sequence

from .linear_algebra import matvec

Vector = tuple[float, ...]
Matrix = tuple[Vector, ...]
FieldFn = Callable[[Vector], Vector]


class StabilityClass(str, Enum):
    STABLE = "STABLE"
    MARGINAL = "MARGINAL"
    UNSTABLE = "UNSTABLE"


@dataclass(frozen=True)
class StabilityReport:
    jacobian: Matrix
    dominant_eigen_abs: float
    residual_norm: float
    classification: StabilityClass


def _vec_add(a: Vector, b: Vector) -> Vector:
    if len(a) != len(b):
        raise ValueError("dim mismatch")
    return tuple(a[i] + b[i] for i in range(len(a)))


def _vec_scale(c: float, a: Vector) -> Vector:
    return tuple(c * x for x in a)


def _norm(a: Vector) -> float:
    return sum(x * x for x in a) ** 0.5


def numerical_jacobian(field_fn: FieldFn, x: Sequence[float], *, eps: float = 1e-6) -> Matrix:
    """중앙차분 Jacobian J_ij = d f_i / d x_j."""
    x0 = tuple(float(v) for v in x)
    n = len(x0)
    f0 = tuple(field_fn(x0))
    if len(f0) != n:
        raise ValueError("field_fn output dim mismatch")
    cols: list[Vector] = []
    for j in range(n):
        e = tuple(1.0 if i == j else 0.0 for i in range(n))
        xp = _vec_add(x0, _vec_scale(eps, e))
        xm = _vec_add(x0, _vec_scale(-eps, e))
        fp = tuple(field_fn(xp))
        fm = tuple(field_fn(xm))
        if len(fp) != n or len(fm) != n:
            raise ValueError("field_fn output dim mismatch")
        col = tuple((fp[i] - fm[i]) / (2.0 * eps) for i in range(n))
        cols.append(col)
    return tuple(tuple(cols[j][i] for j in range(n)) for i in range(n))


def dominant_eigen_abs_power(a: Sequence[Sequence[float]], *, max_iter: int = 100, tol: float = 1e-10) -> float:
    """Power iteration으로 지배 고유값 절대값 근사."""
    m = tuple(tuple(float(v) for v in row) for row in a)
    n = len(m)
    if n == 0 or any(len(row) != n for row in m):
        raise ValueError("square matrix required")
    x = tuple(1.0 for _ in range(n))
    lam_prev = 0.0
    for _ in range(max_iter):
        y = matvec(m, x)
        ny = _norm(y)
        if ny <= 1e-15:
            return 0.0
        x = tuple(v / ny for v in y)
        z = matvec(m, x)
        lam = abs(sum(x[i] * z[i] for i in range(n)))  # Rayleigh abs
        if abs(lam - lam_prev) <= tol:
            return lam
        lam_prev = lam
    return lam_prev


def classify_discrete_stability(rho_abs: float, *, margin: float = 1e-3) -> StabilityClass:
    """이산계 기준: |lambda_max| < 1 stable."""
    if rho_abs < 1.0 - margin:
        return StabilityClass.STABLE
    if rho_abs <= 1.0 + margin:
        return StabilityClass.MARGINAL
    return StabilityClass.UNSTABLE


def analyze_local_stability(field_fn: FieldFn, x_eq: Sequence[float], *, eps: float = 1e-6) -> StabilityReport:
    """평형점 근방 수치선형화 + 안정성 판정."""
    x = tuple(float(v) for v in x_eq)
    j = numerical_jacobian(field_fn, x, eps=eps)
    rho = dominant_eigen_abs_power(j)
    r = _norm(tuple(field_fn(x)))
    cls = classify_discrete_stability(rho)
    return StabilityReport(jacobian=j, dominant_eigen_abs=rho, residual_norm=r, classification=cls)
