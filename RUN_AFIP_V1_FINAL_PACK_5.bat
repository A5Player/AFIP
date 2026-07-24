@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_AFIP_V1_FINAL_PACK_5.ps1"
exit /b %ERRORLEVEL%
