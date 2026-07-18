@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo AFIP virtual environment not found: %PYTHON%
  exit /b 1
)
echo === AFIP Milestone S Pack 5.6 Validation ===
"%PYTHON%" -m pytest tests\test_milestone_s_pack_5_6.py -q
if errorlevel 1 exit /b %errorlevel%
"%PYTHON%" tools\validate_financial_naming.py
if errorlevel 1 exit /b %errorlevel%
echo Pack 5.6 targeted validation completed.
echo Next: .venv\Scripts\python.exe tools\afip_local_quality_check.py
endlocal
