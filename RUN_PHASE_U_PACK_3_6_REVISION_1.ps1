$ErrorActionPreference = "Stop"
Write-Host "AFIP Phase U Pack 3.6 Revision 1 - Compact Dashboard 1 Header"
Write-Host "Safety: presentation-only patch; execution is not started."
python -m pytest tests/test_phase_u_pack_3_6_revision_1_compact_operations_header.py tests/test_phase_u_dashboard_live_mt5_fields.py tests/test_phase_u_dashboard_internal_authority.py -q
python -m afip.dashboard_ui
Write-Host "Dashboard 1 compact-header validation completed."
