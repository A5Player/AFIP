@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_AFIP_V1_SINGLE_RUNTIME_TRUTH_BIG_PACK.ps1" -ProjectRoot C:\AFIP
pause
