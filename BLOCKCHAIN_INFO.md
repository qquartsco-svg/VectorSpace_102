# VectorSpace_Engine Blockchain Info

## Scope

`VectorSpace_Engine` is published as a standalone module repository.

- Core API: `vector_space_*`, `linear_algebra.py`, `stability.py`, `uncertainty.py`
- Integration API: `integrated_math_pipeline.py`, `engine_step_adapters.py`
- Tests: `tests/`

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
