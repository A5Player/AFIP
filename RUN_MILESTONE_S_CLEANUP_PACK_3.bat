@echo off
set PYTHON=%~dp0.venv\Scripts\python.exe
if not exist "%PYTHON%" exit /b 1
"%PYTHON%" -m tools.afip_cleanup_execution_stop
"%PYTHON%" -m pytest tests\test_milestone_s_cleanup_pack_3.py -v
if errorlevel 1 exit /b 1
"%PYTHON%" -m tools.afip_cleanup_pack_3_source_evidence
