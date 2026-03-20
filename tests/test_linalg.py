"""VectorSpace_Engine 선형대수 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from VectorSpace_Engine import (  # noqa: E402
    basis,
    determinant,
    eye,
    gram_schmidt,
    inverse,
    is_linearly_independent,
    matmul,
    matvec,
    rank,
    solve_linear,
)


def test_matmul_and_eye():
    a = ((1.0, 2.0), (3.0, 4.0))
    i2 = eye(2)
    assert matmul(a, i2) == a


def test_determinant_inverse():
    a = ((4.0, 7.0), (2.0, 6.0))
    det = determinant(a)
    assert abs(det - 10.0) < 1e-9
    inv = inverse(a)
    should_be_i = matmul(a, inv)
    assert abs(should_be_i[0][0] - 1.0) < 1e-9
    assert abs(should_be_i[1][1] - 1.0) < 1e-9
    assert abs(should_be_i[0][1]) < 1e-9
    assert abs(should_be_i[1][0]) < 1e-9


def test_solve_linear():
    a = ((3.0, 1.0), (1.0, 2.0))
    b = (9.0, 8.0)
    x = solve_linear(a, b)
    bx = matvec(a, x)
    assert abs(bx[0] - 9.0) < 1e-9
    assert abs(bx[1] - 8.0) < 1e-9


def test_rank_independence_basis():
    v1 = (1.0, 0.0, 0.0)
    v2 = (0.0, 1.0, 0.0)
    v3 = (1.0, 1.0, 0.0)
    assert is_linearly_independent((v1, v2)) is True
    assert is_linearly_independent((v1, v2, v3)) is False
    b = basis((v1, v2, v3))
    assert len(b) == 2
    assert rank(((1.0, 0.0, 1.0), (0.0, 1.0, 1.0), (0.0, 0.0, 0.0))) == 2


def test_gram_schmidt():
    o = gram_schmidt(((1.0, 0.0, 0.0), (1.0, 1.0, 0.0)))
    assert len(o) == 2
    dot12 = sum(x * y for x, y in zip(o[0], o[1]))
    assert abs(dot12) < 1e-9
