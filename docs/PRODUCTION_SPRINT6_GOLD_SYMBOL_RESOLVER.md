# AFIP Production Sprint 6 — GOLD# Symbol Resolver

## Objective
Make AFIP V1 use the official XM gold symbol `GOLD#` first, while keeping a safe fallback resolver for other broker symbol names.

## Changes
- Added `MT5SymbolResolver`.
- Default symbol changed from `XAUUSD` to `GOLD#` for MT5 check flow.
- Connection check now reports both requested symbol and resolved broker symbol.
- Execution remains locked to `LOCKED_SIMULATION_ONLY`.

## Resolver Priority
1. `GOLD#`
2. `GOLD`
3. `XAUUSD#`
4. `XAUUSD`
5. broker-discovered gold-like symbols

## Validation
Run:

```bash
python afip.py mt5-check
python afip.py simulate
pytest tests/test_production_sprint6_gold_symbol_resolver.py
```
