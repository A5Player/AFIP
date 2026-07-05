# AFIP Production Milestone A Pack 8

This pack adds efficiency-aware production maturity to Milestone A.

## Added Files

- `afip/intelligence/liquidity_efficiency_index.py`
- `afip/intelligence/allocation_discipline_index.py`
- `afip/learning/learning_efficiency_score.py`
- `afip/runtime/production_milestone_a_efficiency_runtime.py`
- `tests/test_production_milestone_a_pack_8.py`
- `docs/PRODUCTION_MILESTONE_A_PACK_8.md`
- `AFIP_MILESTONE_A_PACK_8_FILE_LIST.txt`

## Validation

```powershell
pytest tests/test_production_milestone_a.py tests/test_production_milestone_a_pack_2.py tests/test_production_milestone_a_pack_3.py tests/test_production_milestone_a_pack_4.py tests/test_production_milestone_a_pack_5.py tests/test_production_milestone_a_pack_6.py tests/test_production_milestone_a_pack_7.py tests/test_production_milestone_a_pack_8.py
python tools/afip_local_quality_check.py
```

Expected dedicated Milestone A Pack 1-8 tests: 64 passed.
