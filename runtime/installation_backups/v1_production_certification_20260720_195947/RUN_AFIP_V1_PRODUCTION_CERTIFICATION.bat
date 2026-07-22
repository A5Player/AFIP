@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_AFIP_V1_PRODUCTION_CERTIFICATION.ps1" %*
exit /b %errorlevel%
