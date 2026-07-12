@echo off
setlocal
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python tools\afip_four_profile_control.py status || exit /b 1
pytest tests\test_milestone_s_pack_2.py -v || exit /b 1
pytest || exit /b 1
python tools\afip_local_quality_check.py || exit /b 1
python -m afip.dashboard_ui || exit /b 1
python afip.py mt5-check || exit /b 1
echo Milestone S Pack 2 validation completed. LOCKED_SIMULATION_ONLY / NO_ORDER_SENT.
endlocal
