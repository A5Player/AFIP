@echo off
setlocal

echo === AFIP Milestone Q Pack 2 Validation ===
pytest tests/test_milestone_q_pack_2.py -v
if errorlevel 1 exit /b %errorlevel%

pytest
if errorlevel 1 exit /b %errorlevel%

python tools/afip_local_quality_check.py
if errorlevel 1 exit /b %errorlevel%

python -m afip.dashboard_ui
if errorlevel 1 exit /b %errorlevel%

echo Milestone Q Pack 2 validation completed successfully.
endlocal
