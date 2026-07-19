# AFIP Phase U Pack 3.3.2 — M30 Historical Collection & Data Lake Integration

Adds append-only persistence of normalized closed MT5 OHLC bars to the AFIP financial data lake, including M30. Historical coverage now reads the canonical timeframe registry. This pack is research-only and does not change execution, risk, lot sizing, SL, TP, or profile policy.

## Safety
Stop active AFIP research writers before applying or validating this patch.

## Validation
Run `RUN_PHASE_U_PACK_3_3_2.ps1` or `RUN_PHASE_U_PACK_3_3_2.bat`.
