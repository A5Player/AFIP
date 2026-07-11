# Validation — Milestone R Pack 1

Run from the AFIP repository root:

```powershell
pytest tests/test_milestone_r_pack_1.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

Then commit:

```powershell
git add .
git commit -m "Milestone R Pack 1 Production Regression Audit"
git push
```

Expected safety state:

- Execution: `LOCKED_SIMULATION_ONLY`
- Direct execution: `False`
- Live execution: `Disabled`
- Order status: `NO_ORDER_SENT`
- Production Certification: `False`
- Release Candidate: `False`
