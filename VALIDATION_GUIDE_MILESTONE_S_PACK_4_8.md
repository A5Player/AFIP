# Validation Guide — Milestone S Pack 4.8

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "C:\AFIP"

.\RUN_MILESTONE_S_PACK_4_8.ps1
```

Expected:
- Pack regression passes.
- Full pytest passes.
- Financial naming passes.
- Dashboard rebuild completes.

VPS after pull:

```powershell
python tools\afip_demo_execution_control.py stop-all
python tools\afip_demo_execution_control.py start-all
python tools\afip_dashboard_live_control.py stop
python tools\afip_dashboard_live_control.py start
```
