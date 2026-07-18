@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" ( echo Virtual environment Python not found. & exit /b 1 )
.venv\Scripts\python.exe -m pytest tests\test_milestone_s_pack_6_0.py -v || exit /b 1
.venv\Scripts\python.exe tools\afip_local_quality_check.py || exit /b 1
echo Pack 6.0 validation complete. Execution authority remains NONE.
