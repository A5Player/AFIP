$ErrorActionPreference = 'Stop'

Write-Host '=== AFIP Phase U Pack 2 - Two Separate Dashboards ==='

python -m pytest -q tests/test_phase_u_pack_2_two_dashboards.py tests/test_production_milestone_h_pack_9.py tests/test_production_milestone_h_pack_10.py tests/test_phase_u_pack_1_runtime_coverage_dashboard.py tests/test_phase_u_pack_1_1_dashboard_backward_compatibility.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'Dashboard 1: runtime\dashboard\afip_profiles_dashboard.html'
Write-Host 'Dashboard 2: runtime\dashboard\afip_intelligence_research_dashboard.html'
Write-Host 'Phase U Pack 2 validation and dashboard build completed.'
