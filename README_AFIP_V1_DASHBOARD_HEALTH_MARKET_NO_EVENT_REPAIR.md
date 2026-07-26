# AFIP V1 Dashboard Health, Market & No-Event Semantics Repair

Patch-only dashboard repair. No trading logic, capital, lot, SL/TP, routing, or order-send authority is changed.

## Repairs

- Fresh MT5 profile data always overrides stale final-integration snapshots.
- A stopped runtime with fresh MT5 data is shown as `IDLE`, not `STALE`.
- Gateway current state becomes `INACTIVE` while runtime is stopped.
- Current reason becomes `runtime_not_currently_running`.
- No execution event is shown as `NONE_RECORDED` with no fake timestamp or `0 sec` age.
- Weekend market state is shown as `CLOSED_WEEKEND` using read-only UTC calendar inference.
- Runtime, MT5, gateway, and market evidence sources are displayed separately.
- Missing decision/regime/SL/TP evidence is displayed as `NOT_EVALUATED` or `NO_ACTIVE_POSITION`, not invented `WAIT 0%` values.

## Install

Copy the files in this pack over the matching paths under `C:\AFIP`.

## Validate

```powershell
cd C:\AFIP
python -m pytest
python tools\afip_mt5_multi_terminal_check.py
python -m afip.dashboard_ui
Start-Process C:\AFIP\runtime\dashboard\afip_dashboard.html
```

Expected regression total after installation: `2711 passed`.

For continuous read-only refresh:

```powershell
.\RUN_AFIP_V1_DASHBOARD_LIVE_COMPLETE.ps1 -IntervalSeconds 10
```
