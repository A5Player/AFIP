$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Phase U Pack 3 - Three Dashboards and Real Data Integrity ==="
python -m pytest -q tests/test_phase_u_pack_3_three_dashboards.py tests/test_phase_u_pack_2_two_dashboards.py tests/test_phase_u_pack_1_1_dashboard_backward_compatibility.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Dashboard 1: runtime\dashboard\afip_profiles_dashboard.html"
Write-Host "Dashboard 2: runtime\dashboard\afip_intelligence_engine_dashboard.html"
Write-Host "Dashboard 3: runtime\dashboard\afip_research_data_dashboard.html"
