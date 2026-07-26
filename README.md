# AFIP V1 Dashboard Completeness & Live Refresh

Patch-only, read-only dashboard repair.

## Adds

- `afip_dashboard_completeness.html`
- Explicit per-profile field coverage and missing-field evidence
- Research `AVAILABLE`, `NOT_GENERATED`, and `DATA_UNAVAILABLE` separation
- Continuous read-only refresh mode:
  `python -m afip.dashboard_ui --live 10`
- One PowerShell launcher:
  `RUN_AFIP_V1_DASHBOARD_LIVE_COMPLETE.ps1`

## Safety

- No trading logic changes
- No capital, lot, SL, or TP calculations
- No `order_check` or `order_send`
- Missing values are never invented

## Install

Copy all files over the AFIP project root, preserving folders.

## Validate

```powershell
cd C:\AFIP
python -m pytest
python tools\afip_mt5_multi_terminal_check.py
python -m afip.dashboard_ui
```

Expected regression after this patch: `2707 passed` when installed over the user's current 2704-test repository.

## Live mode

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_AFIP_V1_DASHBOARD_LIVE_COMPLETE.ps1 -IntervalSeconds 10
```

Press `Ctrl+C` to stop the read-only live dashboard service.
