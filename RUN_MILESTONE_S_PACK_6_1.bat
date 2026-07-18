@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0RUN_MILESTONE_S_PACK_6_1.ps1"
if errorlevel 1 exit /b 1
endlocal
