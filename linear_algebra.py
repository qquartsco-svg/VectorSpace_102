"""범용 선형대수 유틸리티 (표준 라이브러리 only)."""

from __future__ import annotations

import math
from typing import Sequence

Vector = tuple[float, ...]
Matrix = tuple[Vector, ...]


def _as_vector(v: Sequence[float]) -> Vector:
    return tuple(float(x) for x in v)


def _as_matrix(a: Sequence[Sequence[float]]) -> Matrix:
    m = tuple(_as_vector(row) for row in a)
    if not m:
        raise ValueError("empty matrix")
    cols = len(m[0])
    if cols == 0:
        raise ValueError("matrix with zero columns")
    if any(len(row) != cols for row in m):
        raise ValueError("ragged matrix")
    return m


def shape(a: Sequence[Sequence[float]]) -> tuple[int, int]:
    m = _as_matrix(a)
    return (len(m), len(m[0]))


def transpose(a: Sequence[Sequence[float]]) -> Matrix:
    m = _as_matrix(a)
    r, c = len(m), len(m[0])
    return tuple(tuple(m[i][j] for i in range(r)) for j in range(c))


def eye(n: int) -> Matrix:
    if n < 1:
        raise ValueError("n must be >= 1")
    return tuple(tuple(1.0 if i == j else 0.0 for j in range(n)) for i in range(n))


def mat_add(a: Sequence[Sequence[float]], b: Sequence[Sequence[float]]) -> Matrix:
    ma = _as_matrix(a)
    mb = _as_matrix(b)
    if shape(ma) != shape(mb):
        raise ValueError("shape mismatch for add")
    return tuple(tuple(x + y for x, y in zip(ra, rb)) for ra, rb in zip(ma, mb))


def mat_scale(c: float, a: Sequence[Sequence[float]]) -> Matrix:
    m = _as_matrix(a)
    return tuple(tuple(c * x for x in row) for row in m)


def matmul(a: Sequence[Sequence[float]], b: Sequence[Sequence[float]]) -> Matrix:
    ma = _as_matrix(a)
    mb = _as_matrix(b)
    ra, ca = len(ma), len(ma[0])
    rb, cb = len(mb), len(mb[0])
    if ca != rb:
        raise ValueError("shape mismatch for matmul")
    bt = transpose(mb)
    return tuple(
        tuple(sum(ma[i][k] * bt[j][k] for k in range(ca)) for j in range(cb)) for i in range(ra)
    )


def matvec(a: Sequence[Sequence[float]], x: Sequence[float]) -> Vector:
    m = _as_matrix(a)
    vx = _as_vector(x)
    r, c = len(m), len(m[0])
    if len(vx) != c:
        raise ValueError("shape mismatch for matvec")
    return tuple(sum(m[i][k] * vx[k] for k in range(c)) for i in range(r))


def _rref_internal(a: Sequence[Sequence[float]], *, eps: float = 1e-12) -> tuple[Matrix, list[int]]:
    m = [list(row) for row in _as_matrix(a)]
    rows = len(m)
    cols = len(m[0])
    pivots: list[int] = []
    r = 0
    for c in range(cols):
        pivot = max(range(r, rows), key=lambda i: abs(m[i][c]))
        if abs(m[pivot][c]) <= eps:
            continue
        m[r], m[pivot] = m[pivot], m[r]
        pv = m[r][c]
        m[r] = [x / pv for x in m[r]]
        for i in range(rows):
            if i == r:
                continue
            f = m[i][c]
            if abs(f) <= eps:
                continue
            m[i] = [m[i][j] - f * m[r][j] for j in range(cols)]
        pivots.append(c)
        r += 1
        if r == rows:
            break
    for i in range(rows):
        for j in range(cols):
            if abs(m[i][j]) <= eps:
                m[i][j] = 0.0
    return tuple(tuple(row) for row in m), pivots


def rref(a: Sequence[Sequence[float]], *, eps: float = 1e-12) -> Matrix:
    rr, _ = _rref_internal(a, eps=eps)
    return rr


def rank(a: Sequence[Sequence[float]], *, eps: float = 1e-12) -> int:
    _, piv = _rref_internal(a, eps=eps)
    return len(piv)


def determinant(a: Sequence[Sequence[float]], *, eps: float = 1e-12) -> float:
    m = [list(row) for row in _as_matrix(a)]
    n, c = len(m), len(m[0])
    if n != c:
        raise ValueError("determinant requires square matrix")
    det = 1.0
    sign = 1.0
    for k in range(n):
        pivot = max(range(k, n), key=lambda i: abs(m[i][k]))
        if abs(m[pivot][k]) <= eps:
            return 0.0
        if pivot != k:
            m[k], m[pivot] = m[pivot], m[k]
            sign *= -1.0
        pv = m[k][k]
        det *= pv
        for i in range(k + 1, n):
            f = m[i][k] / pv
            for j in range(k + 1, n):
                m[i][j] -= f * m[k][j]
    return sign * det


def inverse(a: Sequence[Sequence[float]], *, eps: float = 1e-12) -> Matrix:
    m = _as_matrix(a)
    n, c = len(m), len(m[0])
    if n != c:
        raise ValueError("inverse requires square matrix")
    aug = [list(row) + list(row_i) for row, row_i in zip(m, eye(n))]
    rr, piv = _rref_internal(aug, eps=eps)
    if len(piv) < n or any(p != i for i, p in enumerate(piv[:n])):
        raise ValueError("matrix is singular")
    return tuple(tuple(rr[i][n + j] for j in range(n)) for i in range(n))


def solve_linear(a: Sequence[Sequence[float]], b: Sequence[float], *, eps: float = 1e-12) -> Vector:
    m = _as_matrix(a)
    vb = _as_vector(b)
    n, c = len(m), len(m[0])
    if n != c:
        raise ValueError("solve_linear requires square matrix")
    if len(vb) != n:
        raise ValueError("shape mismatch in solve_linear")
    inv = inverse(m, eps=eps)
    return matvec(inv, vb)


def is_linearly_independent(vectors: Sequence[Sequence[float]], *, eps: float = 1e-12) -> bool:
    if not vectors:
        return True
    mat = transpose(vectors)
    return rank(mat, eps=eps) == len(vectors)


def basis(vectors: Sequence[Sequence[float]], *, eps: float = 1e-12) -> tuple[Vector, ...]:
    if not vectors:
        return ()
    vecs = tuple(_as_vector(v) for v in vectors)
    mat = transpose(vecs)
    _, piv = _rref_internal(mat, eps=eps)
    return tuple(vecs[i] for i in piv if i < len(vecs))


def gram_schmidt(vectors: Sequence[Sequence[float]], *, eps: float = 1e-12) -> tuple[Vector, ...]:
    ortho: list[Vector] = []
    for v in vectors:
        w = list(_as_vector(v))
        for u in ortho:
            uu = sum(x * x for x in u)
            if uu <= eps:
                continue
            coef = sum(wi * ui for wi, ui in zip(w, u)) / uu
            w = [wi - coef * ui for wi, ui in zip(w, u)]
        n = math.sqrt(sum(x * x for x in w))
        if n > eps:
            ortho.append(tuple(x / n for x in w))
    return tuple(ortho)
