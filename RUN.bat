@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN.ps1" -ProjectRoot C:\AFIP\source
exit /b %ERRORLEVEL%
