# Production Milestone H Pack 7 — Paper Trading Engine

Pack 7 adds a paper-only trading layer for order lifecycle, unit allocation, portfolio values, AFIP Bank dashboard values, and order explainability.

## Scope

- Paper Trading Engine Runtime
- Paper Order Lifecycle
- Paper Portfolio and Equity
- AFIP Bank values for paper mode
- Unit system enforcement: 1 Unit = 0.01 lot
- Dashboard Runtime dependency for Paper Trading
- No live execution
- XM + GOLD# Version 1 policy

## Explainability

Each paper order exposes reasons for waiting, entry, holding, stop-loss review, break-even review, trailing review, partial close, final exit, alternative decision, current AI reasoning, risk status, and expected next review.

## Safety

Paper Trading never sends broker orders and blocks live execution flags. Lot size is not increased directly. The runtime only increases approved Unit count.
