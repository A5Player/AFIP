@echo off
set PYTHON=%~dp0.venv\Scripts\python.exe
if not exist "%PYTHON%" (
  echo Virtual environment Python not found: %PYTHON%
  exit /b 1
)
"%PYTHON%" tools\afip_demo_execution_control.py stop-all
"%PYTHON%" -m pytest tests\test_milestone_s_cleanup_pack_1.py -v
if errorlevel 1 exit /b 1
"%PYTHON%" tools\afip_architecture_inventory.py
