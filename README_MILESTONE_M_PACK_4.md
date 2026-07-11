# AFIP Milestone M Pack 4 — Pattern Clustering

## Purpose

This pack adds deterministic, market-regime-aware clustering for research patterns produced by the Pattern Knowledge Engine and validated by Pattern Similarity Search.

## Scope

- Partition patterns by Market Regime.
- Require canonical feature schemas within each regime.
- Build deterministic similarity graphs and connected clusters.
- Generate deterministic cluster identifiers.
- Calculate cluster centroids and average internal similarity.
- Preserve source lineage for every cluster.
- Detect duplicate Pattern IDs, schema mismatches, future leakage, and safety-policy violations.
- Keep all outputs research-only.

## Safety

- Broker: XM only.
- Symbol: GOLD# only.
- Base unit: 0.01 lot.
- Execution: `LOCKED_SIMULATION_ONLY`.
- Direct execution: disabled.
- Live execution: disabled.
- Order status: `NO_ORDER_SENT`.
- Production Knowledge Approval: disabled.

## Validation

```powershell
pytest tests/test_milestone_m_pack_4.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git

```powershell
git add .
git commit -m "Milestone M Pack 4 Pattern Clustering"
git push
```
