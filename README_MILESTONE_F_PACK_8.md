# Production Milestone F Pack 8 - Validation

## Scope

Pack 8 adds a deterministic validation layer for AI integration output before Production Readiness.

## Architecture

- Market Regime before Signal Context.
- Data First Architecture.
- Knowledge First Architecture.
- Deterministic runtime only.
- Financial terminology only.
- No production writes from validation output.

## Added Runtime

- `afip.validation.ValidationRuntime`
- `afip.runtime.production_milestone_f_validation_runtime.run_production_milestone_f_validation`

## Validation Behavior

The validation layer accepts AI integration evidence, normalizes percentage fields, groups profiles by market regime before signal context, calculates evidence quality, validation score, approved runtime weight, and validation state.

Validation can return:

- `VALIDATION_WAIT`
- `VALIDATION_BLOCKED`
- `VALIDATION_REVIEW_REQUIRED`
- `VALIDATION_READY`

## Required Checks

```powershell
pytest tests/test_production_milestone_f_pack_8.py -v
pytest
python tools/afip_local_quality_check.py
```
