@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_PHASE_U_PACK_3_3_11.ps1" -RepositoryRoot "%~dp0"
if errorlevel 1 exit /b %errorlevel%
endlocal
