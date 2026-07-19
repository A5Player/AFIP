@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_PHASE_U_PACK_3_4_9.ps1"
if errorlevel 1 (
  echo AFIP Phase U Pack 3.4.9 failed.
  exit /b %errorlevel%
)
