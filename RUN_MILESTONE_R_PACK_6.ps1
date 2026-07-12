$ErrorActionPreference = "Stop"
pytest tests/test_milestone_r_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone R Pack 6 validation completed." -ForegroundColor Green
