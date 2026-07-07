# Production Milestone F Pack 6 - Runtime Adaptation

## Purpose

Pack 6 adds the Runtime Adaptation Engine. It converts validated strategy evolution candidates into deterministic runtime adaptation plans without writing live runtime values automatically.

## Production Rules

- Patch only.
- Financial terminology only.
- Market regime before signal context.
- Data First Architecture.
- Knowledge First Architecture.
- Strategy evolution required before runtime adaptation.
- Runtime plan only; no automatic runtime writes.
- Deterministic output.
- Backward compatible with all previous packs.

## Added Runtime

`afip.runtime.production_milestone_f_runtime_adaptation_runtime.run_production_milestone_f_runtime_adaptation(records)`

## Validation

Run:

```powershell
pytest tests/test_production_milestone_f_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
```
