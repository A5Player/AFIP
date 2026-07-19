@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_PHASE_U_PACK_3_3_1.ps1"
if errorlevel 1 exit /b %errorlevel%
endlocal
