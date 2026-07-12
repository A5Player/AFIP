# Validation — Milestone R Pack 13

- Targeted test: `8 passed`
- Full pytest: `1759 passed`
- AFIP Local Quality Check: `PASS`
- Financial Naming Validation: `PASS`
- MT5 Data Check: `PASS`
- Dashboard Build: `PASS`
- Execution: `LOCKED_SIMULATION_ONLY`
- Direct Execution: `False`
- Live Execution: `Disabled`
- Order Status: `NO_ORDER_SENT`

Commands:

```powershell
pytest tests/test_milestone_r_pack_13.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
