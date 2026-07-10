# AFIP Milestone K Pack 6 — Trailing Stop Intelligence

## Purpose
Adds deterministic trailing-stop review for paper/demo simulation. The module evaluates break-even readiness, profit locking, multi-stage trailing, BUY/SELL stop geometry, trading cost, risk, timing, and market structure.

## Safety Policy
- Broker: XM only
- Symbol: GOLD# only
- 1 Unit = 0.01 Lot
- Execution: LOCKED_SIMULATION_ONLY
- Direct execution: False
- Live execution: Disabled
- Order status: NO_ORDER_SENT

## Main Output
The runtime reports current and proposed stop loss, minimum and estimated locked profit, trailing stage, holding reason, trailing-stop reason, expected next action, confidence, and next review time. English and Thai explanations are visible in the dashboard.

## Validation
Run `RUN_MILESTONE_K_PACK_6.ps1` or `RUN_MILESTONE_K_PACK_6.bat` from the repository root.
