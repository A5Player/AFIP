$ErrorActionPreference = "Stop"
pytest tests/test_regression_patch_1_dashboard_panel_registration.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Regression Patch 1 validation completed." -ForegroundColor Green
