# AFIP Milestone M Pack 5 — Pattern Statistics

## Purpose

Adds deterministic, auditable research statistics for individual Patterns and Pattern Clusters.

## Capabilities

- Pattern-level and Cluster-level statistics
- Sample count, win/loss/breakeven count, and win rate
- Average R-Multiple and expectancy
- Gross profit R, gross loss R, and profit factor
- R-Multiple standard deviation
- Explicit sample-confidence tier
- Chronological outcome validation
- Pattern and Cluster lineage validation
- Deterministic statistics identity and ordering
- Future-leakage protection
- Research-only knowledge authority
- Bilingual dashboard panel

## Safety

- Broker: XM only
- Symbol: GOLD# only
- Base Unit: 0.01 lot
- Execution: LOCKED_SIMULATION_ONLY
- Direct Execution: false
- Live Execution: disabled
- Order Status: NO_ORDER_SENT
- Production Knowledge Approval: false

Pattern statistics do not change trading decisions and do not authorize broker requests or order transmission.

## Validation

```powershell
pytest tests/test_milestone_m_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Next

Milestone M Pack 6 — Pattern Validation.
