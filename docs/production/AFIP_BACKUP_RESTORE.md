# AFIP Backup and Restore Guide

## Backup Scope

Back up the following:

- Repository state.
- Runtime reports.
- Production event logs.
- Paper trading records.
- Configuration files.
- AFIP project database.

## Backup Timing

- Before every patch.
- After every successful production validation.
- Weekly during paper trading.
- Before any live readiness change.

## Restore Procedure

1. Stop AFIP runtime.
2. Confirm MT5 is not executing live orders from AFIP.
3. Restore the repository or checkout the last known good commit.
4. Restore configuration and runtime records.
5. Run full pytest.
6. Run `python tools/afip_local_quality_check.py`.
7. Run `python afip.py mt5-check`.
8. Resume only after all checks pass.
