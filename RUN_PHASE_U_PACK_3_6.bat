@echo off
setlocal
python -m pytest tests/test_phase_u_pack_3_6_dashboard_authority.py tests/test_phase_u_dashboard_home_runtime_fix.py tests/test_phase_u_dashboard_internal_authority.py tests/test_phase_u_dashboard_live_mt5_fields.py tests/test_phase_u_dashboard_live_progress.py -q
if errorlevel 1 exit /b 1
python -m afip.dashboard_ui
if errorlevel 1 exit /b 1
echo Pack 3.6 targeted validation completed. Run full pytest separately.
