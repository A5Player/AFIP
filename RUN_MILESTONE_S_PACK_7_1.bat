@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0RUN_MILESTONE_S_PACK_7_1.ps1"
exit /b %ERRORLEVEL%
