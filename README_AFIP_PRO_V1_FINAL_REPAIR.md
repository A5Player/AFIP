# AFIP Pro V1 Final Repair Pack

Patch-only repair against the supplied latest AFIP source and runtime evidence.

## Repaired

- Publishes live MT5 position details from the existing profile-owned session only.
- Reconciles current MT5 tickets, entry/current price, SL, TP, direction and position count into the dashboard contract.
- Links a live position to the last execution plan only when its ticket matches the recorded execution ticket.
- Uses explicit `UNMATCHED_LIVE_POSITION` when no safe ticket match exists.
- Marks a verified snapshot only when the live snapshot is readable, fresh, connected and labelled LIVE.
- Resolves market status to `OPEN_TICKING` only from fresh valid live tick evidence.
- Replaces stale `waiting_for_runtime_evidence` with `waiting_for_next_runtime_cycle` only when Runtime, MT5 and Gateway evidence are all fresh.
- Keeps legacy inactive semantics and regression compatibility.

## Safety boundary

This pack does not initialize MT5, reconnect, log in, check orders, send orders, calculate lots, alter capital/risk policy, or grant execution authority.

## Install

Stop AFIP workers first, but MT5 terminals may remain open.

```powershell
cd <extracted-pack-folder>
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_AFIP_PRO_V1_FINAL_REPAIR.ps1 -ProjectRoot C:\AFIP
```

## Validate

```powershell
cd C:\AFIP
.\.venv\Scripts\Activate.ps1
.\RUN_AFIP_PRO_V1_FINAL_REPAIR.ps1 -ProjectRoot C:\AFIP
```

Then start AFIP normally and refresh the dashboard after 30–60 seconds.

```powershell
.\START_AFIP.ps1 -ProjectRoot C:\AFIP
Start-Sleep -Seconds 60
Start-Process "C:\AFIP\runtime\dashboard\afip_dashboard.html"
```
