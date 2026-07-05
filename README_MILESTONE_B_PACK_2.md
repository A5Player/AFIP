# AFIP Production Milestone B Pack 2

## Adaptive Weight Engine

This pack adds production-ready adaptive weighting for Milestone B.

### Files

- `afip/fusion/adaptive_weight_engine.py`
- `afip/fusion/regime_weight_profile.py`
- `afip/fusion/performance_weight_adjustment.py`
- `afip/fusion/intelligence_weight_matrix.py`
- `afip/runtime/production_milestone_b_weight_runtime.py`
- `docs/PRODUCTION_MILESTONE_B_PACK_2.md`
- `tests/test_production_milestone_b_pack_2.py`
- `AFIP_MILESTONE_B_PACK_2_FILE_LIST.txt`

### Validation

```powershell
pytest tests/test_production_milestone_b_pack_2.py
python tools/afip_local_quality_check.py
```
