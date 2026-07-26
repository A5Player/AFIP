# AFIP V1 Pipeline Scroll & Current/Historical Evidence Repair

Patch-only dashboard repair.

## Changes

- Enables reliable vertical scrolling inside the Command Center iframe.
- Replaces meta-refresh with JavaScript refresh that stores and restores scroll position.
- Adds a 240 px bottom safe area so Windows taskbar does not cover the final pipeline rows.
- Historical or inactive execution evidence is no longer presented as current PASS/BLOCKED state.
- Current stage status becomes NOT_EVALUATED while the last recorded result remains visible as `Last evidence`.
- Trading logic, authority calculations, MT5 initialization and order send are unchanged.

## Install

Copy the files over the repository root, then run:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
python -m pytest
python -m afip.dashboard_ui
Start-Process C:\AFIP\runtime\dashboard\afip_dashboard.html
```

Restart live dashboard refresh if required:

```powershell
.\RUN_AFIP_V1_DASHBOARD_LIVE_COMPLETE.ps1 -IntervalSeconds 10
```
