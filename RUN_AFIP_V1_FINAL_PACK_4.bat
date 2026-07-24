@echo off
set ROOT=%~1
if "%ROOT%"=="" set ROOT=C:\AFIP\source
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_AFIP_V1_FINAL_PACK_4.ps1" -ProjectRoot "%ROOT%"
exit /b %ERRORLEVEL%
