# AFIP Milestone R Pack 1 — Production Regression Audit

## Purpose

Adds a deterministic, immutable regression-audit layer for the first stage of Milestone R Production Certification.

## Scope

The audit validates:

- Milestone Q Pack 10 completion lineage
- Baseline and current full-test counts
- Targeted regression-suite evidence
- Full pytest evidence
- AFIP Local Quality Check evidence
- Dashboard build evidence
- Financial Naming Validation evidence
- MT5 Data Check evidence
- Evidence uniqueness and chronology
- Permanent XM / GOLD# / 0.01-lot-unit policy
- `LOCKED_SIMULATION_ONLY` and `NO_ORDER_SENT`

## Important Boundary

A passing regression audit does **not** grant Production Certification, Release Candidate status, direct execution, live execution, broker requests, order transmission, or position modification.

## Validation

```powershell
pytest tests/test_milestone_r_pack_1.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Next

Milestone R Pack 2 — Duplicate Code Audit.
