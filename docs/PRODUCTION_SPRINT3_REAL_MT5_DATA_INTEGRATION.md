# AFIP Production Sprint 3 — Real MT5 Data Integration

## Status
PASS

## Goal
Connect AFIP V1 to real MT5 market/account data safely while keeping all execution locked.

## Delivered
- `python afip.py mt5-check`
- MT5 package availability check
- MT5 terminal initialize check
- Symbol select check
- Real tick reader
- Real OHLC reader for M1/M5/M15/H1/H4/D1
- Symbol information reader
- Account information reader
- Spread calculation from real tick
- Simulation fallback if MT5 is missing, disabled, or incomplete
- Fake MT5 tests for tick, account, symbol, OHLC, and fallback behavior

## Safety
- No order sending
- No live execution
- DEMO remains locked
- LIVE remains locked
- Output is data/readiness only

## Commands
```powershell
python afip.py mt5-check
python afip.py mt5-check XAUUSD
python afip.py simulate
```

## Result Meaning
- `READY` means MT5 market data can be read.
- `FALLBACK_READY` means AFIP remains safe and runnable using simulation fallback.
- `LOCKED_SIMULATION_ONLY` confirms execution is still blocked.

## Next Sprint
Production Sprint 4 — Real Indicator Intelligence
- EMA Intelligence
- ATR Intelligence
- RSI Intelligence
- MACD Intelligence
- ADX Intelligence
- Bollinger Band Intelligence
- VWAP Intelligence
