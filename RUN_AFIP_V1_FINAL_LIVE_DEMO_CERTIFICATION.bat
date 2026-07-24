@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_AFIP_V1_FINAL_LIVE_DEMO_CERTIFICATION.ps1"
exit /b %ERRORLEVEL%
