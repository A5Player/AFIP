# AFIP Milestone Q Pack 5 — Market Intent Stability Validation

## Purpose

Validate whether accepted Pack 4 Market Intent statistics remain stable across strictly ordered research windows.

## Added

- `afip/market_intent_stability_validation/__init__.py`
- `afip/market_intent_stability_validation/runtime.py`
- `tests/test_milestone_q_pack_5.py`
- `RUN_MILESTONE_Q_PACK_5.ps1`
- `RUN_MILESTONE_Q_PACK_5.bat`

## Validation Coverage

The runtime validates Pack 4 lineage, unique identifiers, non-overlapping chronology, statistical coverage, metric ranges, persistence and intensity ranges, change-rate ranges, dominant-pattern consistency, stable-window ratio, data quality, future safety, prerequisite ordering, and Version 1.0 frozen execution policy.

The output is deterministic, immutable, and research-only. It cannot update parameters, change trading logic, promote production knowledge, modify positions, create broker requests, or transmit orders.

Execution remains `LOCKED_SIMULATION_ONLY`; live execution remains disabled; order status remains `NO_ORDER_SENT`.
