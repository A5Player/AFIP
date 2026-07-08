# AFIP Production Operations Checklist

## Daily Checks

- Confirm VPS is online.
- Confirm MT5 is connected.
- Confirm `GOLD#` is selected and data is updating.
- Review AFIP simulation or paper trading output.
- Review spread caution and risk status.
- Confirm no unexpected live execution mode is enabled.

## Weekly Checks

- Run full pytest.
- Run `python tools/afip_local_quality_check.py`.
- Review production event logs.
- Review runtime metrics for latency or memory drift.
- Create a repository backup.

## Monthly Checks

- Review performance reports.
- Review documentation and operating procedures.
- Confirm broker account settings and symbol naming.
- Confirm backup and restore procedures remain valid.

## Stop Conditions

Stop automated operation and review manually if:

- MT5 data is unavailable.
- Spread remains above acceptable limits.
- Risk gate blocks activity.
- Runtime enters unexpected execution mode.
- Quality check fails.
