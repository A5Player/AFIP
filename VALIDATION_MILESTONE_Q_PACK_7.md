# Milestone Q Pack 7 Validation

Run from the AFIP repository root:

```powershell
pytest tests/test_milestone_q_pack_7.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

Execution must remain:

- `LOCKED_SIMULATION_ONLY`
- Direct Execution = `False`
- Live Execution = `Disabled`
- `NO_ORDER_SENT`

## Verified Result

- Targeted test: 8 passed
- Full pytest: 1631 passed
- AFIP Local Quality Check: PASS
- Financial Naming Validation: PASS
- MT5 Data Check: PASS
- Dashboard Build: PASS
