# Validation — Milestone R Pack 7

```powershell
pytest tests/test_milestone_r_pack_7.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

Expected policy state: `LOCKED_SIMULATION_ONLY`, direct execution disabled, live execution disabled, `NO_ORDER_SENT`.
