# AFIP V1 Runtime Truth & Passive Monitoring Final

Patch-only repair built from `AFIP(62).zip`.

## Repairs

- Default MT5 monitoring is passive and never calls `MetaTrader5.initialize()`.
- Windows terminal detection works without requiring `psutil`; it falls back to PowerShell/CIM and matches each configured executable path.
- `CONNECTED_PASSIVE` means the exact configured terminal process is running. `DISCONNECTED` means that process is absent.
- Active broker/login diagnostics require the explicit `--active` switch.
- Active verification stores `mt5_live_snapshot.json`; passive observation never converts an old snapshot into live financial evidence.
- Dashboard separates monitor freshness from live financial freshness.
- `Fresh` can no longer coexist misleadingly with `Connection ERROR` and unavailable financial data.
- Runtime, MT5 process state, financial evidence, and snapshot age are separate fields.
- No lot, SL, TP, signal, risk, execution authority, or order-send logic changed.

## Install

Stop the dashboard live loop with `Ctrl+C`, extract this pack, then run:

```powershell
cd <EXTRACTED_PACK_FOLDER>
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_AFIP_V1_RUNTIME_TRUTH_PASSIVE_MONITORING_FINAL.ps1 -ProjectRoot C:\AFIP
```

## Commands

Passive observation; never opens a terminal:

```powershell
cd C:\AFIP
python tools\afip_mt5_multi_terminal_check.py
```

Explicit active diagnostic; may initialize/connect configured terminals:

```powershell
python tools\afip_mt5_multi_terminal_check.py --active
```

## Expected close test

With P1/P2 open and P3/P4 closed, passive output should show:

```text
P1 CONNECTED_PASSIVE
P2 CONNECTED_PASSIVE
P3 DISCONNECTED
P4 DISCONNECTED
monitoring_mode PASSIVE
```

The passive command must not reopen P3 or P4.
