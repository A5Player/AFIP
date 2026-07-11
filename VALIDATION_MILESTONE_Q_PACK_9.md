# Validation — Milestone Q Pack 9

```powershell
pytest tests/test_milestone_q_pack_9.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

Execution must remain `LOCKED_SIMULATION_ONLY`; Direct Execution and Live Execution must remain disabled; order status must remain `NO_ORDER_SENT`.
