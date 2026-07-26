AFIP V1 MT5 Existing Session IPC Fix

This patch removes portable=True from the two MT5 runtime authorities so AFIP
targets the manually opened P1-P4 sessions instead of launching separate portable
instances.

Files inspected:
- tools\afip_verify_account_isolation.py
- afip\demo_execution_gateway\runtime.py

Install:
cd <extracted folder>
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_AFIP_V1_MT5_EXISTING_SESSION_IPC_FIX.ps1 -ProjectRoot C:\AFIP

Then confirm exactly four terminal64.exe processes remain and run:
cd C:\AFIP
.\START_AFIP.ps1

This patch does not change lot size, SL/TP, signal thresholds, risk, or order policy.
