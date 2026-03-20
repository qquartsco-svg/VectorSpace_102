"""
GlobalSystemVector v0 + 공통 엔진 스텝 결과 (운영 수학 OS 계약 초안).

CMP 01~20 서브그래프와 별개로, Nexus/런타임이 들고 다닐 최상위 상태 스냅샷.
verdict 최종 부여는 Observer/Runtime 권장 — 수학 엔진은 observation·omega 기여만.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class Verdict(str, Enum):
    """운영 판정. 최종 문자열은 보통 한 레이어(Observer/Runtime)에서만 부여."""

    JUST = "JUST"
    STABLE = "STABLE"
    FRAGILE = "FRAGILE"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class EngineStepResult:
    """단일 엔진(또는 플러그인) 한 스텝의 공통 출력."""

    engine_id: str
    state: Mapping[str, float]
    derived: Mapping[str, float]
    observation: Mapping[str, float]
    verdict: Verdict | None = None
    history: tuple[float, ...] = ()


@dataclass
class GraphRefV0:
    """CMP-16/17 연동용 가벼운 그래프 핸들(정본 그래프는 외부 모듈)."""

    graph_id: str
    n_nodes: int = 0
    edge_count: int = 0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VectorAxisSpec:
    """상태벡터 축 메타데이터.

    상용/공학 계산기에서 각 축의 의미를 잃지 않도록 label/unit/domain을 명시한다.
    """

    key: str
    label: str
    unit: str = ""
    domain: str = "generic"


@dataclass
class GlobalSystemVectorV0:
    """
    필드/우주선 런타임이 한 스텝에 들고 다닐 최상위 상태 벡터 스냅샷.

    - x: 물리·인지 상태를 하나의 실수 벡터로 평탄화한 것 (차원은 도메인별 고정 권장)
    - fields: 스칼라 장 요약(전위·온도·압력 등) 키-값
    - omega: 종합 건강도 [0,1] 근사
    """

    schema_version: str = "0.1"
    x: tuple[float, ...] = ()
    fields: dict[str, float] = field(default_factory=dict)
    graph_ref: GraphRefV0 | None = None
    omega: float = 1.0
    verdict: Verdict | None = None
    history_ptr: tuple[float, ...] = ()
    meta: dict[str, Any] = field(default_factory=dict)
    axes: tuple[VectorAxisSpec, ...] = ()
