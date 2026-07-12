# Validation — Milestone R Pack 4

```powershell
pytest tests/test_milestone_r_pack_4.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui

git add .
git commit -m "Milestone R Pack 4 Production Architecture Audit"
git push
```

Required execution state: `LOCKED_SIMULATION_ONLY`, direct execution disabled, live execution disabled, `NO_ORDER_SENT`.
