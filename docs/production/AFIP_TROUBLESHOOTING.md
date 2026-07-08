# AFIP Troubleshooting Guide

## First checks
Run:

```powershell
python tools/afip_local_quality_check.py
```

If it fails, review the section that failed: financial naming, simulation, MT5 data check, or pytest.

## MT5 data issue
Run:

```powershell
python afip.py mt5-check
```

Confirm symbol resolution, tick availability, account visibility, and timeframe candles.

## Spread or risk warning
Keep execution locked to simulation. Review trading cost intelligence and risk intelligence before changing configuration.

## Regression
Stop deployment and run full pytest. Roll back to the latest commit where local quality check passed.
