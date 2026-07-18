@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=%CD%\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo AFIP virtual-environment Python not found: %PYTHON%
  exit /b 1
)
echo === AFIP Milestone S Pack 5.7 Validation ===
"%PYTHON%" -m pytest tests\test_milestone_s_pack_5_7.py -q || exit /b 1
"%PYTHON%" tools\validate_financial_naming.py || exit /b 1
echo Pack 5.7 targeted validation completed.
echo Next: .\.venv\Scripts\python.exe tools\afip_local_quality_check.py
endlocal
