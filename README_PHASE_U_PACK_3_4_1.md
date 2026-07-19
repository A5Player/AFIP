# AFIP Phase U Pack 3.4.1

## Historical Dataset Readiness Certification

This pack introduces deterministic certification of historical OHLC datasets before comprehensive walk-forward research.

It verifies required timeframe presence, OHLC integrity, duplicate timestamps, input ordering, temporal gaps, estimated missing records, coverage duration, quality ratios, and research eligibility.

Certification statuses:

- `READY` — dataset meets research quality requirements.
- `CAUTION` — dataset may be used with explicit quality evidence and restricted interpretation.
- `QUARANTINED` — dataset must not enter research ranking or evidence promotion.

Required timeframes are M1, M5, M15, M30, H1, H4, and D1.

The certifier is execution-neutral. It does not change profile policy, position sizing, drawdown limits, order execution, SL, or TP.

## VPS certification command

```powershell
python tools/afip_historical_dataset_certify.py `
  --input runtime\historical_data\gold_history.jsonl `
  --instrument GOLD# `
  --source-id XM_VPS_HISTORY `
  --output runtime\research\certification\historical_dataset_readiness.json
```

The input may be JSONL, JSON, or CSV. Each record must include timeframe, timestamp, open, high, low, and close fields.
