# Production Batch 14.8 — Final Mode Compatibility Fix

## Purpose

Finalize local quality gate compatibility for `RealMarketDataIntelligenceWiring` tests.

## Change

The Sprint 7 compatibility test now accepts both:

- `REAL_MARKET_DATA` when full provider data is available
- `SIMULATION_FALLBACK` when compatibility fallback data is used

This keeps the test aligned with the current AFIP runtime behavior while preserving production safety.

## Validation

Run:

```bash
python tools/afip_local_quality_check.py
```

Expected result:

```text
Status: PASS
```
