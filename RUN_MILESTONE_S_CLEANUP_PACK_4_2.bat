@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_MILESTONE_S_CLEANUP_PACK_4_2.ps1"
exit /b %ERRORLEVEL%
