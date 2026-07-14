# Validation Guide — Milestone S Pack 4.1

```powershell
python -m pytest tests/test_milestone_s_pack_4_1.py -v
python -m pytest -q
python tools/afip_local_quality_check.py
python tools/afip_dashboard_live_control.py start
python tools/afip_dashboard_live_control.py status
start .\runtime\dashboard\afip_dashboard.html
```

Expected: 1805 tests pass, dashboard service RUNNING, P1-P4 cards at the top, and data timestamps refreshing.
