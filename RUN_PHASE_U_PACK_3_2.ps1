$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.2 - Automatic Research Runtime"
python -m pytest tests/test_phase_u_pack_3_2_automatic_research_runtime.py tests/test_phase_u_pack_3_1_compact_dashboard_2.py tests/test_phase_u_pack_3_1_2_compact_dashboards_1_and_3.py -q
python afip.py research-bootstrap
python -m afip.dashboard_ui
Write-Host "PASS - Automatic research bootstrap completed and Dashboard 3 updated."
