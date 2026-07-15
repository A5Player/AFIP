# Validation Guide — Milestone S Pack 4.7

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "C:\AFIP"

pytest tests\test_milestone_s_pack_4.py tests\test_milestone_s_pack_4_7.py
pytest
python tools\afip_local_quality_check.py
```

Expected:
- Pack tests: 17 passed
- Full tests: 1812 passed
- Local quality check: PASS
