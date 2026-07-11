# AFIP Milestone Q Pack 6 — Market Intent Drift Detection

## Purpose

Detect deterministic Market Intent drift across accepted Pack 5 stability-validation windows.

## Added

- `afip/market_intent_drift_detection/__init__.py`
- `afip/market_intent_drift_detection/runtime.py`
- `tests/test_milestone_q_pack_6.py`
- `RUN_MILESTONE_Q_PACK_6.ps1`
- `RUN_MILESTONE_Q_PACK_6.bat`

## Detection Coverage

The runtime validates Pack 5 lineage, unique identifiers, non-overlapping chronology, bounded metrics, certified data, future safety, prerequisite ordering, and Version 1.0 frozen execution policy. It measures first-to-last persistence, intensity, stability-score, stable-window-ratio, and dominant-pattern-consistency deltas together with maximum adjacent stability and intensity deltas.

The result reports a deterministic drift score and `NONE`, `LOW`, `MODERATE`, or `HIGH` drift band. Moderate or high drift requires research review only; it does not change parameters or trading logic.

Execution remains `LOCKED_SIMULATION_ONLY`; live execution remains disabled; order status remains `NO_ORDER_SENT`.
