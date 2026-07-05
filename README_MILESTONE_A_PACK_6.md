# AFIP Production Milestone A Pack 6

Production-ready additive continuation for Milestone A.

## Included

- Portfolio maturity index
- Market regime consistency index
- Optimization drift index
- Maturity-aware runtime integration
- Pytest coverage
- Documentation
- File list

## Run

```powershell
pytest tests/test_production_milestone_a.py tests/test_production_milestone_a_pack_2.py tests/test_production_milestone_a_pack_3.py tests/test_production_milestone_a_pack_4.py tests/test_production_milestone_a_pack_5.py tests/test_production_milestone_a_pack_6.py
python tools/afip_local_quality_check.py
```
