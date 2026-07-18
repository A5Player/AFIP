@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0RUN_MILESTONE_T_PACK_2.ps1"
exit /b %ERRORLEVEL%
