# Production Milestone F Pack 5 - Strategy Evolution

## Purpose

Pack 5 adds the Strategy Evolution Engine. It converts validated experience knowledge into deterministic strategy evolution candidates.

## Production Rules

- Patch only.
- Financial terminology only.
- Market regime before signal context.
- Data First Architecture.
- Knowledge First Architecture.
- No runtime strategy writes.
- Deterministic output.
- Backward compatible with all previous packs.

## Added Runtime

`afip.runtime.production_milestone_f_strategy_evolution_runtime.run_production_milestone_f_strategy_evolution(records)`

## Validation

Run:

```powershell
pytest tests/test_production_milestone_f_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
```
