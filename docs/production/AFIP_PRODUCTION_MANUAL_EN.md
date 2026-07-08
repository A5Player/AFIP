# AFIP Production Manual (English)

## Purpose
AFIP is a deterministic trading intelligence runtime for simulation-first production preparation. The system must keep Market Regime before Signal Context and must not send live orders while execution is locked to simulation.

## Runtime Flow
1. Load market data from the configured market data source.
2. Resolve the market regime before reading signal context.
3. Evaluate market intelligence, risk intelligence, cost intelligence, and execution readiness.
4. Produce a deterministic decision report.
5. Record observability, event log, metrics, paper trading, and release candidate evidence.

## Installation
Use the repository root on Windows PowerShell. Install project requirements, connect MT5 when needed, and verify that `python afip.py mt5-check` reports READY before any production review.

## Verification Commands
Run the pack test, full pytest, and local quality check before each commit. Keep execution locked to simulation until a deliberate live-readiness process is completed.

## Recovery
If a production review fails, stop deployment, keep execution locked to simulation, inspect the quality result file, and rollback to the last successful Git commit if required.

## Troubleshooting
Use the local quality check first. Then review simulation output, MT5 data check, feature flags, event log, runtime metrics, and production release candidate report.
