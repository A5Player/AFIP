$ErrorActionPreference = "Stop"
Write-Host "AFIP V1 Final Revision 2.1 - Dashboard Authority Merge"
python -m pytest -q `
  tests/test_afip_v1_final_runtime_observatory.py `
  tests/test_afip_v1_final_revision_2_replay_performance.py `
  tests/test_afip_v1_final_revision_2_1_dashboard_authority_merge.py `
  tests/test_phase_u_final_dashboard_mt5_live.py `
  tests/test_phase_u_pack_3_4_11_unified_research.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Revision 2.1 targeted validation PASS"
