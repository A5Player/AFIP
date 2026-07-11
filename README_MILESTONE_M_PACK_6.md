# AFIP Milestone M Pack 6 — Pattern Validation

## Purpose
Adds deterministic research validation for Pattern-level and Cluster-level statistics.

## Capabilities
- Explicit minimum sample gate
- Minimum expectancy gate
- Minimum profit-factor gate
- Maximum R-dispersion gate
- Pattern and Cluster validation results
- Per-scope rejection reasons
- Statistics lineage validation
- Deterministic validation identity and ordering
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

Pattern validation does not modify trading logic, create broker requests, or authorize order transmission.

## Validation
```powershell
pytest tests/test_milestone_m_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Next
Milestone M Pack 7 — Pattern Explainability.
