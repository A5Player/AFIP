$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.6 - Dashboard Authority Consolidation"
Write-Host "Safety: presentation-only validation; execution and research are not started."
python -m pytest tests/test_phase_u_pack_3_6_dashboard_authority.py tests/test_phase_u_dashboard_home_runtime_fix.py tests/test_phase_u_dashboard_internal_authority.py tests/test_phase_u_dashboard_live_mt5_fields.py tests/test_phase_u_dashboard_live_progress.py -q
python -m afip.dashboard_ui
Write-Host "Pack 3.6 targeted validation completed. Run full pytest separately."
