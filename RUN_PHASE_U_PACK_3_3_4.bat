@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_PHASE_U_PACK_3_3_4.ps1"
exit /b %errorlevel%
