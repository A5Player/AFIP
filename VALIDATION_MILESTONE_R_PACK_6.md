# Validation — Milestone R Pack 6

```powershell
pytest tests/test_milestone_r_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

Required: Production Certification=False; Release Candidate=False; Direct Execution=False; Live Execution=Disabled; Execution=`LOCKED_SIMULATION_ONLY`; Order Status=`NO_ORDER_SENT`.
