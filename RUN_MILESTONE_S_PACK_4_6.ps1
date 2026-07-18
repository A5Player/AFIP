$ErrorActionPreference = "Stop"
$env:PYTHONPATH = (Get-Location).Path
python -m pytest tests\test_milestone_s_pack_4.py tests\test_milestone_s_pack_4_6.py
python -m pytest
python tools\afip_local_quality_check.py
python -m afip.dashboard_ui
