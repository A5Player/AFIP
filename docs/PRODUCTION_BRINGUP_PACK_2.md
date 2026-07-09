# Production Bring-up Pack 2 — MT5 Live Account Dashboard

## Purpose

Pack 2 adds read-only MT5 account telemetry to the Dashboard. It shows broker,
server, masked login, balance, equity, margin, free margin, leverage, currency,
symbol, bid, ask, spread, and last tick time.

## Safety

- Read-only account telemetry only.
- No order sending.
- No trading logic change.
- Live execution remains disabled.
- Version 1 remains XM only and GOLD# only.

## Dashboard

Adds a new panel:

- MT5 Live Account / บัญชี MT5 สด

The System panel also receives MT5 Account, MT5 Server, MT5 Equity, and MT5 Spread
rows so the VPS screen can confirm account connectivity quickly.

## Run

```powershell
pytest tests/test_production_bringup_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
