$ErrorActionPreference = "Stop"
if (-not (Test-Path ".\afip\dashboard_ui")) { throw "Run from AFIP repository root." }
python -m pytest tests/test_phase_u_dashboard_home_runtime_fix.py tests/test_phase_u_pack_3_three_dashboards.py tests/test_phase_u_pack_3_1_compact_dashboard_2.py -q
python -m afip.dashboard_ui
Write-Host "Open: runtime\dashboard\afip_dashboard.html" -ForegroundColor Green
