@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_PHASE_U_PACK_3_1_2.ps1"
exit /b %errorlevel%
