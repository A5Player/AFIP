$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.2.1 - Visible Research Startup Pipeline"
Write-Host ""
Write-Host "[STAGE 1/4] Regression tests"
python -m pytest tests/test_phase_u_pack_3_2_automatic_research_runtime.py tests/test_phase_u_pack_3_2_1_visible_research_pipeline.py tests/test_phase_u_pack_3_1_compact_dashboard_2.py tests/test_phase_u_pack_3_1_2_compact_dashboards_1_and_3.py -q
if ($LASTEXITCODE -ne 0) { throw "Regression tests failed." }

Write-Host ""
Write-Host "[STAGE 2/4] Research bootstrap, MT5 history collection and chronological replay"
python -u afip.py research-bootstrap
if ($LASTEXITCODE -ne 0) { throw "Research bootstrap failed." }

Write-Host ""
Write-Host "[STAGE 3/4] Dashboard rebuild"
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed." }

Write-Host ""
Write-Host "[STAGE 4/4] Opening Research & Data Dashboard"
Start-Process ".\runtime\dashboard\afip_research_data_dashboard.html"
Write-Host "PASS - Research pipeline completed and Dashboard 3 was rebuilt."
Write-Host "Dashboard file: runtime\dashboard\afip_research_data_dashboard.html"
