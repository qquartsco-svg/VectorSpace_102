"""
VectorSpace_Engine — 운영 수학 OS용 벡터공간 계산기 (독립 모듈).

- CMP 01~20 과 별개: **GlobalSystemVector** 스냅샷 + R^n 연산 + Ω 병합.
- 정본: ``2_operational/30_CORTEX_LAYER/VectorSpace_Engine/``
- 허브: ``1_calculator/21_VectorSpace`` (심볼릭 링크)
"""

from .vector_space_calculator import VectorSpaceCalculator
from .integrated_math_pipeline import IntegratedMathPipeline, PipelineConfig
from .vector_space_schema import (
    EngineStepResult,
    GlobalSystemVectorV0,
    GraphRefV0,
    VectorAxisSpec,
    Verdict,
)
from .vector_space_core import (
    VectorSpace,
    add,
    change_basis,
    distance,
    dot,
    norm,
    project_onto_direction,
    scale,
)
from .linear_algebra import (
    basis,
    determinant,
    eye,
    gram_schmidt,
    inverse,
    is_linearly_independent,
    mat_add,
    mat_scale,
    matmul,
    matvec,
    rank,
    rref,
    shape,
    solve_linear,
    transpose,
)
from .engine_step_adapters import (
    from_convergence_dynamics,
    from_semiconductor_observation,
    from_terraforming_plan,
    from_vector_calculus,
    from_wave_snapshot,
)
from .stability import (
    StabilityClass,
    StabilityReport,
    analyze_local_stability,
    classify_discrete_stability,
    dominant_eigen_abs_power,
    numerical_jacobian,
)
from .uncertainty import (
    UncertaintyState,
    confidence_band,
    covariance_predict,
    covariance_update_joseph,
)

__all__ = [
    "VectorSpaceCalculator",
    "IntegratedMathPipeline",
    "PipelineConfig",
    "GlobalSystemVectorV0",
    "EngineStepResult",
    "GraphRefV0",
    "VectorAxisSpec",
    "Verdict",
    "VectorSpace",
    "dot",
    "norm",
    "distance",
    "add",
    "scale",
    "change_basis",
    "project_onto_direction",
    "shape",
    "transpose",
    "eye",
    "mat_add",
    "mat_scale",
    "matmul",
    "matvec",
    "rref",
    "rank",
    "determinant",
    "inverse",
    "solve_linear",
    "is_linearly_independent",
    "basis",
    "gram_schmidt",
    "from_convergence_dynamics",
    "from_vector_calculus",
    "from_wave_snapshot",
    "from_semiconductor_observation",
    "from_terraforming_plan",
    "StabilityClass",
    "StabilityReport",
    "numerical_jacobian",
    "dominant_eigen_abs_power",
    "classify_discrete_stability",
    "analyze_local_stability",
    "UncertaintyState",
    "covariance_predict",
    "covariance_update_joseph",
    "confidence_band",
]
