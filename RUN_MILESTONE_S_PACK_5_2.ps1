$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone S Pack 5.2 Validation ==="
python -m pytest tests/test_milestone_s_pack_5_1.py tests/test_milestone_s_pack_5_2.py
python -m pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "=== Pack 5.2 validation completed ==="
