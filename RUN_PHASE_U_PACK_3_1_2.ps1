$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.1.2 - Compact Dashboards 1 and 3"
python -m pytest -q tests/test_phase_u_pack_3_1_2_compact_dashboards_1_and_3.py tests/test_phase_u_pack_3_1_compact_dashboard_2.py tests/test_phase_u_pack_3_1_1_renderer_compatibility.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "PASS - Dashboards 1, 2 and 3 use compact single-line presentation."
