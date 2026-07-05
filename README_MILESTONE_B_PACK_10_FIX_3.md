# AFIP Production Milestone B Pack 10 Fix 3

Compatibility patch for Pack 5 and Pack 10 decision runtime integration.

## Fix

- Adds backward-compatible `confidence_level` property to `ProductionDecisionRuntimeResult`.
- Preserves Pack 10 `evaluate(..., market_context=..., risk_context=...)` support.
- Preserves Pack 5 `run()` status contract.
- Uses financial / AI terminology only.
