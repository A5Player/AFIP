# Validation — Milestone R Pack 2

Run from the AFIP repository root:

```powershell
pytest tests/test_milestone_r_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

Expected policy state:

```text
LOCKED_SIMULATION_ONLY
Direct Execution = False
Live Execution = Disabled
NO_ORDER_SENT
Production Certification = False
Release Candidate = False
```
