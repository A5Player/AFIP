# Milestone R Pack 6 — Production Safety Audit

Deterministic, immutable validation of reviewed production-safety controls after Repository Cleanup.

Scope: validates R Pack 5 lineage; audits risk-boundary, order-safety, position-safety, data-safety, operational-safety, and fail-safe evidence; requires unique IDs, SHA-256 fingerprints, chronology, review completion, mandatory domain coverage, and passing safety score; blocks failures and frozen-policy violations.

Namespace: `afip.production_certification_safety_audit` preserves the existing `afip.safety_audit` public API.

Execution remains `LOCKED_SIMULATION_ONLY`, live/direct execution disabled, `NO_ORDER_SENT`.

Validation:
```powershell
pytest tests/test_milestone_r_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

Next: Milestone R Pack 7 — Security Audit.
