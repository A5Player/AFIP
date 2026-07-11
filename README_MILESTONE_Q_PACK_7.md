# AFIP Milestone Q Pack 7 — Market Intent Confidence Calibration

## Purpose

Calibrate deterministic research confidence from accepted Pack 6 Market Intent drift reports.

## Added

- `afip/market_intent_confidence_calibration/__init__.py`
- `afip/market_intent_confidence_calibration/runtime.py`
- `tests/test_milestone_q_pack_7.py`
- `RUN_MILESTONE_Q_PACK_7.ps1`
- `RUN_MILESTONE_Q_PACK_7.bat`

## Calibration Coverage

The runtime validates Pack 6 lineage, unique drift identifiers, chronology, drift acceptance, bounded finite metrics, certified data, future safety, Market Regime and Market Behaviour prerequisite ordering, evidence coverage, minimum calibrated confidence, and Version 1.0 frozen execution policy.

It produces raw drift confidence, evidence coverage, persistence consistency, intensity consistency, stability consistency, pattern consistency, calibrated confidence, and a `HIGH`, `MODERATE`, `CAUTIOUS`, or `INSUFFICIENT` confidence band.

The result remains immutable and research-only. It cannot update parameters, change trading logic, promote production knowledge, modify positions, create broker requests, transmit orders, or grant Production Certification.

Execution remains `LOCKED_SIMULATION_ONLY`; live execution remains disabled; order status remains `NO_ORDER_SENT`.
