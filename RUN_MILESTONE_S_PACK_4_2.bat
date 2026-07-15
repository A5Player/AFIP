@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%"
.venv\Scripts\python.exe -m pytest tests\test_milestone_s_pack_4.py tests\test_milestone_s_pack_4_1.py || exit /b 1
.venv\Scripts\python.exe -m pytest || exit /b 1
.venv\Scripts\python.exe tools\afip_local_quality_check.py || exit /b 1
.venv\Scripts\python.exe afip.py mt5-check || exit /b 1
.venv\Scripts\python.exe -m afip.dashboard_ui || exit /b 1
endlocal
