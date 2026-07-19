@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_MILESTONE_T_PACK_6.ps1"
exit /b %ERRORLEVEL%
