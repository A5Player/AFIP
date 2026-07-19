# AFIP Phase U Pack 3.3.1 — Universal Timeframe Registry

This patch establishes one deterministic timeframe registry for historical collection, chronological replay, research participation, gap detection and dashboards.

Supported order after this pack:

`M1, M5, M15, M30, H1, H4, D1`

## Changes

- Adds `afip/timeframe_registry.py` as the canonical ordered registry.
- Adds complete M30 metadata and MT5 constant resolution.
- Connects the automatic research collector and replay loop to the registry.
- Connects the historical download pipeline to the registry.
- Keeps `TimeframeAdapter` backward compatible while removing its duplicated definition list.
- Does not change live trading policy, risk thresholds, position sizing, SL, TP or execution authority.
- Does not delete or rewrite historical/research data.

## Install and validate

Stop any AFIP runtime writing to research files, extract this ZIP into the AFIP repository root, then run:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_PHASE_U_PACK_3_3_1.ps1
```

M5 replay coverage remains an open evidence-based investigation. This pack does not label the 1,441/2,000 result as expected or defective.
