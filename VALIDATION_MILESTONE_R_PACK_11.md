# Milestone R Pack 11 Validation

Required commands:

```powershell
pytest tests/test_milestone_r_pack_11.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

Expected permanent execution state:

```text
Production Certification = Granted by valid Pack 10 evidence
Release Candidate         = Not Granted
Version 1.0 Final         = Not Granted
Direct Execution          = False
Live Execution            = Disabled
Execution                 = LOCKED_SIMULATION_ONLY
Order Status              = NO_ORDER_SENT
```
