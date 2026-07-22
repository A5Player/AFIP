@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_AFIP_V1_FINAL_INTEGRATION.ps1" %*
exit /b %errorlevel%
