@echo off
setlocal
python -m pytest tests/test_phase_u_pack_3_6_revision_1_compact_operations_header.py tests/test_phase_u_dashboard_live_mt5_fields.py tests/test_phase_u_dashboard_internal_authority.py -q
if errorlevel 1 exit /b %errorlevel%
python -m afip.dashboard_ui
if errorlevel 1 exit /b %errorlevel%
echo Dashboard 1 compact-header validation completed.
