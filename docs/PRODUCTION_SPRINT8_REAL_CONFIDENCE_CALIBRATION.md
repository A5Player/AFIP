# Production Sprint 8 — Real Confidence Calibration

## Objective
Align official Modular Intelligence confidence with Risk and Simulation Order protection.

## Why
Sprint 7 connected real GOLD# OHLC data to Modular Intelligence, but Risk could still block an order using the older multi-timeframe score, creating a mismatch such as:

- Modular Intelligence: BUY / Confidence 100
- Risk: confidence_below_minimum
- Order: NO_ORDER

## Implementation
Added `ConfidenceCalibrator` to make Risk use the official Modular Intelligence decision confidence while keeping hard protection active.

Hard protection remains active:

- Spread limit
- Regime penalty limit
- Position count limit
- Execution lock

## Files
- `afip/risk/confidence_calibrator.py`
- `afip/runtime/runtime_v1.py`
- `tests/test_production_sprint8_real_confidence_calibration.py`

## Validation
- `python afip.py simulate`
- `pytest -q tests/test_production_sprint8_real_confidence_calibration.py tests/test_production_sprint7_real_market_data_intelligence_wiring.py`

## Status
PASS — SIMULATION ONLY. LIVE execution remains locked.
