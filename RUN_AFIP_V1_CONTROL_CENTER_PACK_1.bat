@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_AFIP_V1_CONTROL_CENTER_PACK_1.ps1" -ProjectRoot "C:\AFIP\source"
exit /b %ERRORLEVEL%
