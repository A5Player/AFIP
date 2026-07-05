# AFIP Production Sprint 12 — Market Structure Intelligence

## Status
Ready for validation.

## Objective
Add Market Structure Intelligence to evaluate swing highs, swing lows, bullish structure, bearish structure, and confirmed structure breaks from OHLC data.

## Scope
- Added `MarketStructureIntelligence`.
- Registered it in the official Intelligence catalog.
- Updated simulation console output to show structure state.
- Kept execution locked to simulation only.
- Used financial market terminology only.

## Validation
Run:

```bash
python tools/validate_financial_naming.py
python afip.py simulate
python afip.py mt5-check
```

Expected result:
- Naming validation passes.
- Simulation runs with 15 Intelligence components.
- MT5 check remains read-only and uses `GOLD#`.
