# AFIP Milestone M Pack 1 — Knowledge Intelligence Foundation

Establishes deterministic, versioned, explainable research knowledge records after Milestone L completion.

## Scope
- Validates chronology, unique IDs, market regime, feature/outcome schemas, source lineage, explainability, data quality, and future-leakage controls.
- Approves research knowledge only.
- Does not enable pattern search, clustering, production knowledge, broker requests, or order transmission.
- Preserves XM Only, GOLD# Only, 1 Unit = 0.01 Lot, and LOCKED_SIMULATION_ONLY.

## Validation
```powershell
pytest tests/test_milestone_m_pack_1.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
