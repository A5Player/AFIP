$ErrorActionPreference = "Stop"
Write-Host "AFIP V1 Final Revision 2.2 - Runtime Progress Authority Fix"
python -m pytest tests/test_afip_v1_final_runtime_observatory.py tests/test_afip_v1_final_revision_2_replay_performance.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Revision 2.2 validation PASS"
