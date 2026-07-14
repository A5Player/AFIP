# Milestone S Pack 4 — Demo Execution Gateway

AFIP can transmit protected `GOLD#` orders only after the gateway proves the configured MT5 account is a **DEMO** account (`trade_mode=0`). Real and contest accounts are blocked before `order_send`.

## Profile policies

- P1 High Safety: USD 1,000 capital per fixed 0.01 unit, minimum confidence 98.
- P2 Balanced: USD 500 capital per fixed 0.01 unit, minimum confidence 95.
- P3 High Risk Within Plan: USD 200 capital per fixed 0.01 unit, minimum confidence 90.
- P4 Research: USD 100 capital per fixed 0.01 unit, minimum confidence 60.
- Maximum three independent 0.01 units per profile.

## Mandatory gates

XM only, `GOLD#` only, exact account/server match, MT5 demo trade mode, expert trading allowed, real MT5 data only, risk pass, trading-cost pass, protected order ready, SL/TP present, no manual position, local two-level arm, unit capacity, and duplicate cooldown.

Validation never arms execution and never sends an order.
