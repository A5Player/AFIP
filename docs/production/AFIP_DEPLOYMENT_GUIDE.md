# AFIP Production Deployment Guide

This guide prepares AFIP for controlled deployment on a Windows VPS with MT5 while keeping execution locked until the operator intentionally changes production controls.

## Deployment Principles

- Keep the repository under version control.
- Use patch-only updates.
- Validate every update with pytest and the local quality check.
- Keep MT5 connected and confirm the symbol resolver still selects `GOLD#`.
- Keep execution locked to simulation or paper trading until live readiness is explicitly approved.

## Windows VPS Preparation

1. Install Python compatible with the validated local environment.
2. Install Git.
3. Install MetaTrader 5 from the selected broker.
4. Clone the AFIP repository.
5. Create a dedicated runtime directory for reports, logs, backups, and paper trading output.
6. Run the full validation command block before enabling any scheduled runtime.

## MT5 Preparation

1. Log in to the broker account.
2. Confirm the active account number and broker server.
3. Confirm `GOLD#` is visible in Market Watch.
4. Run `python afip.py mt5-check`.
5. Confirm M1, M5, M15, H1, H4, and D1 data are available.

## Startup Preparation

Use Windows Task Scheduler or a supervised command shell only after validation passes. The startup command must call a script that first verifies the working directory and Python environment.

## Pre-Deployment Gate

Do not proceed unless all of the following pass:

```powershell
pytest
python tools/afip_local_quality_check.py
python afip.py mt5-check
```
