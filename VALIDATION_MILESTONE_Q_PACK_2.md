# AFIP Milestone Q Pack 2 — Validation

```powershell
pytest tests/test_milestone_q_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui

git add .
git commit -m "Milestone Q Pack 2 Market Intent State Normalization"
git push
```

Execution must remain `LOCKED_SIMULATION_ONLY` with `NO_ORDER_SENT`.

## Verified result in build environment

- Targeted test: 8 passed
- Full pytest: 1591 passed
- AFIP Local Quality Check: PASS
- Dashboard Build: PASS
- Financial Naming Validation: PASS
