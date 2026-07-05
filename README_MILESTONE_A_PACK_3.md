# AFIP Production Milestone A Pack 3

Production Milestone A Pack 3 adds a production decision bridge on top of Pack 1 and Pack 2.

## Files

- `afip/intelligence/adaptive_weight_allocator.py`
- `afip/intelligence/regime_exposure_controller.py`
- `afip/learning/learning_stability_monitor.py`
- `afip/runtime/production_milestone_a_decision_bridge.py`
- `tests/test_production_milestone_a_pack_3.py`
- `docs/PRODUCTION_MILESTONE_A_PACK_3.md`
- `AFIP_MILESTONE_A_PACK_3_FILE_LIST.txt`

## Validation

```powershell
pytest tests/test_production_milestone_a.py tests/test_production_milestone_a_pack_2.py tests/test_production_milestone_a_pack_3.py
python tools/afip_local_quality_check.py
```
