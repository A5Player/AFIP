# Validation Guide — Milestone S Pack 4.6

```powershell
pytest tests\test_milestone_s_pack_4.py tests\test_milestone_s_pack_4_6.py
pytest
python tools\afip_local_quality_check.py
python -m afip.dashboard_ui
```

On VPS, stop and restart all demo runtimes after pulling the commit so the new policy is loaded.
