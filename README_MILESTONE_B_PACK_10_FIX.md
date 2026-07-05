# AFIP Production Milestone B Pack 10 Fix

This fix restores backward compatibility for `ProductionMilestoneBDecisionRuntime.run()` while preserving the decision runtime interface.

## Validation

```powershell
pytest tests/test_production_milestone_b_pack_5.py tests/test_production_milestone_b_pack_10.py
python tools/afip_local_quality_check.py
```
