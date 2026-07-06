# Production Milestone C Pack 15 - Learning Foundation

Pack 15 adds the deterministic learning foundation for AFIP Production Milestone C.

## Scope

- Regime-first learning observations.
- Learning profile repository grouped by market regime before signal family.
- Learning governance for bounded parameter update candidates.
- Runtime adapter for deterministic production validation.
- Pack-specific tests and one-command scripts.

## Architecture Rules

- Financial terminology only.
- Market Regime before Signal.
- Data First Architecture.
- Knowledge First Architecture.
- Runtime remains deterministic.
- No production execution behavior is changed.

## Validation

```powershell
pytest tests/test_production_milestone_c_pack_15.py -v
pytest
python tools/afip_local_quality_check.py
```

## Runtime

```powershell
python afip/runtime/production_milestone_c_learning_foundation_runtime.py
```
