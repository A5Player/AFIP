$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.5 Revision 1 - Dashboard Import Compatibility"
Write-Host "Safety: this script does not start execution."
python -m pytest tests/test_phase_u_dashboard_live_progress.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -c "from afip.dashboard_ui.live_research_dashboard import build; print('Import check: PASS')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Revision 1 targeted validation completed. Run full pytest separately."
