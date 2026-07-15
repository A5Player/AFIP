$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot
& .\.venv\Scripts\python.exe -m pytest tests\test_milestone_s_pack_4.py tests\test_milestone_s_pack_4_1.py
& .\.venv\Scripts\python.exe -m pytest
& .\.venv\Scripts\python.exe tools\afip_local_quality_check.py
& .\.venv\Scripts\python.exe afip.py mt5-check
& .\.venv\Scripts\python.exe -m afip.dashboard_ui
