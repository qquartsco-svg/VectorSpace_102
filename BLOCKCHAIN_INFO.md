# VectorSpace_Engine Blockchain Info

## 역할

`VectorSpace_Engine`는 `ENGINE_HUB` 운영 수학 OS가 공유하는
벡터공간 상태 스키마와 선형대수 계산기를 제공합니다.

- `GlobalSystemVectorV0` 스냅샷 계약
- `VectorSpaceCalculator` 상태공간 계산
- `IntegratedMathPipeline` 수학 레이어 압축 판정

## 정본 위치

- 정본:
  - `/Users/jazzin/Desktop/00_BRAIN/02_SYSTEMS/ENGINE_HUB/2_operational/30_CORTEX_LAYER/VectorSpace_Engine`
- 계산기 허브 노출:
  - `ENGINE_HUB/1_calculator/21_VectorSpace`

## 핵심 파일

- `__init__.py`
- `vector_space_core.py`
- `vector_space_calculator.py`
- `vector_space_schema.py`
- `linear_algebra.py`
- `integrated_math_pipeline.py`

## 계약 원칙

- 외부 의존성 없이 표준 라이브러리만 사용
- 최종 `Verdict` 부여는 Observer/Runtime 층과의 역할 분리를 유지
- 테스트는 `tests/` 아래 canonical 기준으로 유지
