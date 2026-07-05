# AFIP Production Sprint 7 — Real Market Data Intelligence Wiring

## Goal
Connect read-only MT5 `GOLD#` OHLC data to the official Modular Intelligence pipeline.

## Completed
- Added `RealMarketDataIntelligenceWiring`.
- `python afip.py simulate` now attempts real MT5 `GOLD#` OHLC first.
- Intelligence output now reports data status, data source, and primary timeframe.
- Execution remains locked: `LOCKED_SIMULATION_ONLY`.
- Safe fallback remains active when MT5 or market data is unavailable.

## Safety Rule
Sprint 7 reads market data only. It does not send, modify, or close orders.

## Validation
```bash
python afip.py simulate
python afip.py mt5-check
pytest -q tests/test_production_sprint7_real_market_data_intelligence_wiring.py
```
