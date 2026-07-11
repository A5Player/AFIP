# Milestone Q Pack 3 Validation

Run from the AFIP repository root:

```powershell
pytest tests/test_milestone_q_pack_3.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

After all checks pass:

```powershell
git add .
git commit -m "Milestone Q Pack 3 Market Intent Sequence Analysis"
git push
```

Required execution state remains:
- `LOCKED_SIMULATION_ONLY`
- `Direct Execution = False`
- `Live Execution = Disabled`
- `NO_ORDER_SENT`

## Verified Build Result
- Targeted test: 8 passed
- Full pytest: 1599 passed
- AFIP Local Quality Check: PASS
- Financial Naming Validation: PASS
- MT5 Data Check: PASS
- Dashboard Build: PASS
