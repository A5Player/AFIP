$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.1 - Compact Dashboard 2"
python -m pytest tests/test_phase_u_pack_3_1_compact_dashboard_2.py tests/test_phase_u_pack_3_three_dashboards.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Dashboard 2 compact layout generated."
Write-Host "Open: runtime\dashboard\afip_intelligence_engine_dashboard.html"
