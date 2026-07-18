@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_MILESTONE_S_PACK_7_2_2.ps1"
exit /b %ERRORLEVEL%
