@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_MILESTONE_S_PACK_7_3.ps1"
exit /b %ERRORLEVEL%
