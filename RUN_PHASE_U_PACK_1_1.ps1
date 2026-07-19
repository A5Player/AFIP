$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Phase U Pack 1.1 ==="
Write-Host "Dashboard Backward Compatibility Patch"

python -m pytest -q tests/test_phase_u_pack_1_1_dashboard_backward_compatibility.py tests/test_production_milestone_h_pack_9.py tests/test_production_milestone_h_pack_10.py
python tools/validate_financial_naming.py
python -m pytest -q
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui

Write-Host "Phase U Pack 1.1 validation and dashboard build completed."
