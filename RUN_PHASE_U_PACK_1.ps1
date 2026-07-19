$ErrorActionPreference="Stop"
python -m pytest -q tests/test_phase_u_pack_1_runtime_coverage_dashboard.py
python tools/validate_financial_naming.py
python -m pytest -q
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Phase U Pack 1 validation and dashboard build completed."
