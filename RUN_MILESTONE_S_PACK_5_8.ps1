$ErrorActionPreference = "Stop"
$python = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
& $python -m pytest tests/test_milestone_s_pack_5_8.py
& $python tools/validate_financial_naming.py
Write-Host "Milestone S Pack 5.8 validation completed. Execution authority remains NONE."
