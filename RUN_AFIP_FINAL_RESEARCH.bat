@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_AFIP_FINAL_RESEARCH.ps1" %*
exit /b %ERRORLEVEL%
