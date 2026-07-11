# AFIP Milestone P Pack 8 — Market Behaviour Validation Governance

This patch adds a deterministic governance gate for accepted Pack 7 market-behaviour confidence calibration reports.

## Scope

- Validate Pack 7 calibration lineage and unique `PBCF-` identifiers.
- Validate chronology and future-leakage protection.
- Require Market Regime evaluation before Market Behaviour.
- Validate evidence coverage and confidence thresholds.
- Enforce AFIP Version 1.0 Feature Freeze policy version.
- Enforce separation between research review and production certification roles.
- Require documented manual review in Pack 9.
- Preserve all adaptive, production, position, broker, and execution locks.

## Safety

This runtime is research-only. It cannot update parameters, change trading logic, promote production knowledge, modify positions, create broker requests, or transmit orders.

## Validation

- Targeted tests: 8 passed
- Full regression: 1559 passed
- AFIP Local Quality Check: PASS
- Dashboard generation: PASS
