# AFIP Milestone P Pack 7 — Market Behaviour Confidence Calibration

This patch adds deterministic, research-only confidence calibration for accepted Milestone P Pack 6 market-behaviour drift reports.

## Scope

- Validate Pack 6 report lineage and unique report IDs.
- Validate chronology, data quality, future safety, and Market Regime before Behaviour.
- Measure transition evidence coverage.
- Score persistence, regime-change, behaviour-change, and stable-window stability.
- Produce a bounded calibrated confidence score and confidence band.
- Preserve immutable records and all Version 1.0 execution locks.

## Safety

This runtime cannot update parameters, change trading logic, promote production knowledge, modify positions, create broker requests, or transmit orders.

Execution remains `LOCKED_SIMULATION_ONLY`, direct execution remains false, live execution remains disabled, and order status remains `NO_ORDER_SENT`.
