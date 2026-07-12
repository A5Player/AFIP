@echo off
setlocal

pytest tests/test_milestone_r_pack_2.py -v
if errorlevel 1 exit /b %errorlevel%

pytest
if errorlevel 1 exit /b %errorlevel%

python tools\afip_local_quality_check.py
if errorlevel 1 exit /b %errorlevel%

python -m afip.dashboard_ui
if errorlevel 1 exit /b %errorlevel%

endlocal
