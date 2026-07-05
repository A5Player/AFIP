# Production Milestone B Pack 14 — Position Valuation Layer

Pack 14 extends the AFIP production accounting chain after position accounting and exposure reconciliation.

## Capability
The pack values open positions using market price data, calculates unrealized profit and loss, and reconciles valuation results against return limits before downstream portfolio reporting.

## Controls
- Ledger readiness validation
- Market price availability validation
- Unrealized PnL state classification
- Maximum absolute return ratio control
- Deterministic review routing for incomplete valuation data

## Validation
- `pytest tests/test_production_milestone_b_pack_14.py -v`
- `pytest`
- `python tools/afip_local_quality_check.py`

## Status
Production-ready incremental pack.
