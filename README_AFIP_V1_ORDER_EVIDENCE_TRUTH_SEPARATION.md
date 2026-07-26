# AFIP V1 Order Evidence Truth Separation

Patch-only dashboard repair. No trading, sizing, SL/TP, routing, MT5 initialization, or order-send logic is changed.

## Repair

- Separates current runtime truth from the last historical execution evidence.
- Historical `ORDER_SENT` and `BLOCKED` values are no longer displayed as current order states.
- Adds current runtime, gateway, order status, permission, execution authority, and current reason.
- Keeps historical decision, authority, order parameters, MT5 result, tickets, timestamp, age, and source paths for audit.
- Preserves the four-column desktop comparison layout.

## Install

Copy all files over `C:\AFIP`, then run:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
python -m pytest
python -m afip.dashboard_ui
Start-Process C:\AFIP\runtime\dashboard\afip_dashboard.html
```

Expected regression result for the assembled source used to build this patch:

```text
2737 passed
```
