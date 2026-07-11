# AFIP Milestone M Pack 2 — Pattern Knowledge Engine

Builds canonical, deterministic research patterns from validated knowledge records.

## Scope
- Requires Milestone M Pack 1 Knowledge Intelligence Foundation approval.
- Normalizes feature vectors into stable pattern identities.
- Partitions patterns by market regime.
- Aggregates duplicate pattern identities without duplicating stored knowledge.
- Records accepted/rejected outcomes and R-multiple statistics.
- Preserves source lineage, data-quality certification, and future-leakage protection.
- Enables pattern statistics and validation only.
- Does not enable similarity search, clustering, production knowledge approval, broker requests, or order transmission.
- Preserves XM Only, GOLD# Only, 1 Unit = 0.01 Lot, and LOCKED_SIMULATION_ONLY.

## Validation
```powershell
pytest tests/test_milestone_m_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
