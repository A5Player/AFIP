@echo off
setlocal
python -m pytest tests/test_phase_u_dashboard_live_progress.py -q
if errorlevel 1 exit /b %errorlevel%
python -c "from afip.dashboard_ui.live_research_dashboard import build; print('Import check: PASS')"
if errorlevel 1 exit /b %errorlevel%
echo Revision 1 targeted validation completed. Run full pytest separately.
