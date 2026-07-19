$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.1.1 - Renderer Compatibility Fix"
python -m pytest tests/test_phase_u_pack_3_1_compact_dashboard_2.py tests/test_phase_u_pack_3_1_1_renderer_compatibility.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "PASS - Dashboard 2 renderer compatibility restored."
