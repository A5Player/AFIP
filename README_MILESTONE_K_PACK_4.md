# Milestone K Pack 4 — Dynamic Stop Loss Intelligence

Adds deterministic, explainable stop-loss review for XM GOLD# paper/demo simulation.

## Controls
- Validates BUY/SELL stop geometry.
- A move must reduce risk distance.
- Requires an open position, approved risk, valid timing, and confirmed market structure.
- Keeps 1 Unit = 0.01 Lot.
- Never sends or modifies a live order.

## Validation
Run `RUN_MILESTONE_K_PACK_4.ps1` or `RUN_MILESTONE_K_PACK_4.bat`.
