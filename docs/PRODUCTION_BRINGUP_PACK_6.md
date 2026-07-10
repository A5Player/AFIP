# Production Bring-up Pack 6 — AFIP Bank Live

Adds a deterministic, read-only capital ledger for XM / GOLD# paper and demo operation. It separates external deposits and withdrawals from closed and floating trading profit, then exposes balance, equity, reserve, available allocation and lifetime return to the dashboard.

## Safety
Live execution remains disabled. The runtime cannot transfer funds, submit orders, or modify trading decisions. Unsupported broker, symbol, live mode, and invalid withdrawal state are blocked with explicit reasons.

## Inputs
`initial_capital`, `deposits`, `withdrawals`, `closed_profit`, `floating_profit`, `reserve`, and optional `bank_transactions`.

## Validation
Run `RUN_PRODUCTION_BRINGUP_PACK_6.ps1` or `.bat`.
