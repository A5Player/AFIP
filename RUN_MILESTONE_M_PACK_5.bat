@echo off
setlocal

python -m pytest tests/test_milestone_m_pack_5.py -v
if errorlevel 1 exit /b %errorlevel%

python -m pytest
if errorlevel 1 exit /b %errorlevel%

python tools\afip_local_quality_check.py
if errorlevel 1 exit /b %errorlevel%

python -m afip.dashboard_ui
if errorlevel 1 exit /b %errorlevel%

echo Milestone M Pack 5 validation completed successfully.
endlocal
