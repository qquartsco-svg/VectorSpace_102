# VectorSpace_Engine Blockchain Info

## Scope

`VectorSpace_Engine` is published as a standalone module repository.

- Core API: `vector_space_*`, `linear_algebra.py`, `stability.py`, `uncertainty.py`
- Integration API: `integrated_math_pipeline.py`, `engine_step_adapters.py`
- Tests: `tests/`

## PHAM Contribution Rule

- GNJz(Qquarts) contribution cap: blockchain-verifiable maximum **6%**
- GNJz(Qquarts)는 그 어떤 상황에서도 자신의 기여도를 **6%를 넘기지 않는다**.
- This 6% rule applies only to GNJz(Qquarts) as a self-imposed authorship and merit ceiling.
- The rule does not redefine other contributors' ownership or repository-wide contribution ratios.

## Signature Policy

- Signature mode: SHA-256 content manifest
- Manifest file: `SIGNATURE.sha256`
- Verification command:

```bash
shasum -a 256 -c SIGNATURE.sha256
```

## Integrity Rules

- All files listed in `SIGNATURE.sha256` must validate (`OK`).
- Any hash mismatch means the published artifact changed.
- This module does not require external engine files for unit tests.
- `PHAM_BLOCKCHAIN_LOG.md` records release scope, version, and verification intent.
- `SIGNATURE.sha256` is the canonical file-by-file hash record for this standalone release.
