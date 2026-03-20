"""유클리드 상태공간 R^n — 내적·노름·사영·거리·기저변환 (순수 표준 라이브러리)."""

from __future__ import annotations

import math
from typing import Sequence

from .linear_algebra import inverse, matvec


def _vec_check(a: Sequence[float], b: Sequence[float]) -> None:
    if len(a) != len(b):
        raise ValueError(f"dim mismatch: {len(a)} vs {len(b)}")


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    _vec_check(a, b)
    return float(sum(x * y for x, y in zip(a, b)))


def add(a: Sequence[float], b: Sequence[float]) -> tuple[float, ...]:
    _vec_check(a, b)
    return tuple(x + y for x, y in zip(a, b))


def scale(c: float, a: Sequence[float]) -> tuple[float, ...]:
    return tuple(c * x for x in a)


def norm(a: Sequence[float]) -> float:
    return math.sqrt(dot(a, a))


def distance(a: Sequence[float], b: Sequence[float]) -> float:
    return norm(tuple(x - y for x, y in zip(a, b)))


def project_onto_direction(
    v: Sequence[float], u: Sequence[float], *, eps: float = 1e-15
) -> tuple[float, ...]:
    """v를 단위 방향 u에 사영한 벡터 (u는 정규화되지 않아도 됨)."""
    _vec_check(v, u)
    uu = dot(u, u)
    if uu < eps:
        raise ValueError("zero direction for projection")
    coef = dot(v, u) / uu
    return scale(coef, u)


def change_basis(
    x: Sequence[float],
    basis_from: Sequence[Sequence[float]],
    basis_to: Sequence[Sequence[float]],
) -> tuple[float, ...]:
    """좌표벡터 x 를 from-basis 에서 to-basis 로 변환한다.

    basis 행렬은 "열벡터가 기저"인 표준 형태를 따른다.
    """
    x_from = tuple(float(v) for v in x)
    std = matvec(basis_from, x_from)
    to_inv = inverse(basis_to)
    return matvec(to_inv, std)


class VectorSpace:
    """차원 고정 R^n — 상태공간 계산기의 수학적 바닥."""

    __slots__ = ("dim",)

    def __init__(self, dim: int) -> None:
        if dim < 1:
            raise ValueError("dim must be >= 1")
        self.dim = dim

    def zero(self) -> tuple[float, ...]:
        return tuple(0.0 for _ in range(self.dim))

    def assert_dim(self, v: Sequence[float]) -> None:
        if len(v) != self.dim:
            raise ValueError(f"expected dim {self.dim}, got {len(v)}")
