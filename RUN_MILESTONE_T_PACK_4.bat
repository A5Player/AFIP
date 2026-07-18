@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_MILESTONE_T_PACK_4.ps1"
exit /b %ERRORLEVEL%
