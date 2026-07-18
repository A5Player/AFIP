# Validation Guide — Milestone S Pack 4.9

```powershell
cd C:\AFIP
.\.venv\Scripts\Activate.ps1

python tools\afip_demo_execution_control.py stop-all
python -m pytest tests\test_milestone_s_pack_4_9_emergency_execution_safety.py -v
python tools\afip_pack_4_9_source_audit.py
pytest
python tools\afip_local_quality_check.py
git status
```

Expected focused result: 6 passed.

Do not restart the demo runner until the execution gateway is wired to call
`approve_execution()` immediately before `order_check` and `order_send`.
