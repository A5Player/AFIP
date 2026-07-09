# Production Bring-up Pack 4 — Market Session & Trading Calendar Monitor

## Scope

Pack 4 adds a read-only market calendar layer for XM GOLD# demo and paper runtime. It explains market open, market close, weekend detection, holiday detection, Asia session, London session, New York session, trading allowed, trading block reason, dashboard live market status, and next review time.

## Production Policy

- Broker: XM only.
- Symbol: GOLD# only.
- Live execution: disabled.
- Paper and demo runtime: allowed.
- Trading logic changed: false.
- Dashboard telemetry only: true.

## Source

New source files:

- `afip/market_calendar/__init__.py`
- `afip/market_calendar/models.py`
- `afip/market_calendar/runtime.py`

Modified source files:

- `afip/dashboard_ui/runtime.py`
- `afip/dashboard_ui/launcher.py`

## Runtime

`MarketCalendarRuntime.evaluate_one(record)` returns `MarketCalendarReport` with:

- market open / closed status
- weekend status
- holiday status and holiday name
- Asia / London / New York session flags
- active sessions
- primary session
- trading allowed
- trading block reason
- dashboard live market status
- next review time

The runtime accepts deterministic `current_time_utc` for testing and dashboard reproducibility. Configured holidays may be passed through `holiday_calendar` or `holidays`.

## Dashboard

The dashboard now includes a `market_calendar` panel and upgrades the existing `market` panel to use live market calendar telemetry. The dashboard displays the important decision fields required by the no-black-box policy:

- Trading Allowed
- Trading Block Reason
- Dashboard Live Market Status
- Next Review Time

## Tests

Run:

```powershell
pytest tests/test_production_bringup_pack_4.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

Expected policy result:

- Targeted Pack 4 tests: pass
- Full pytest: pass
- AFIP Local Quality Check: PASS
- Dashboard generation: PASS

## Safety

This pack does not enable live trading, does not send orders, and does not modify order execution logic. It is operational market status telemetry for explainable dashboard display only.
