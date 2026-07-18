@echo off
setlocal
set PYTHON=python
if exist .venv\Scripts\python.exe set PYTHON=.venv\Scripts\python.exe
%PYTHON% -m pytest tests\test_milestone_s_pack_5_8.py || exit /b 1
%PYTHON% tools\validate_financial_naming.py || exit /b 1
echo Milestone S Pack 5.8 validation completed. Execution authority remains NONE.
