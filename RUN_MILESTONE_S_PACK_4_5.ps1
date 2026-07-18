$ErrorActionPreference = "Stop"
pytest tests\test_milestone_s_pack_4.py
pytest
python tools\afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone S Pack 4.5 validation completed."
