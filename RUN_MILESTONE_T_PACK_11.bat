@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_MILESTONE_T_PACK_11.ps1"
exit /b %ERRORLEVEL%
