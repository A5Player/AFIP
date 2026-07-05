# AFIP Production Sprint 13 — Liquidity Intelligence

## Status
Ready for validation.

## Objective
Upgrade AFIP liquidity analysis using real OHLC market data from `GOLD#`.

## Scope
- Added financial-standard `LiquidityIntelligence`.
- Replaced the older quality-based liquidity component in the official Intelligence catalog.
- Added equal-high and equal-low liquidity pool detection.
- Added buy-side and sell-side liquidity sweep detection.
- Added spread and range condition penalties.
- Updated simulation console output with a dedicated Liquidity Intelligence section.
- Kept execution locked to simulation only.

## Validation
Run:

```bash
python tools/validate_financial_naming.py
python afip.py simulate
python afip.py mt5-check
```

Expected result:
- Financial naming validation passes.
- Simulation runs with 15 Intelligence components.
- Liquidity Intelligence section appears in the console.
- MT5 check remains read-only and uses `GOLD#`.
