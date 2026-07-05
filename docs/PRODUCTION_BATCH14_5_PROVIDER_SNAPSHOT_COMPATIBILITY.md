# Production Batch 14.5 — Provider Snapshot Compatibility Fix

## Objective
Stabilize the local quality gate by allowing RealMarketDataIntelligenceWiring to run with test providers that expose a single snapshot API instead of the full timeframe_snapshots API.

## Changes
- Keep full timeframe_snapshots support for production providers.
- Add compatibility fallback for snapshot/get_snapshot providers used by tests.
- Preserve LOCKED_SIMULATION_ONLY execution safety.
- Maintain Financial Naming Standard compliance.

## Validation
Run:

```bash
python tools/afip_local_quality_check.py
```
