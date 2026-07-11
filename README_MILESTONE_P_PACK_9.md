# AFIP Milestone P Pack 9 — Market Behaviour Review Certification

This patch adds deterministic certification of documented manual research review for accepted Pack 8 Market Behaviour Validation Governance reports.

## Scope

- Validate unique `PBGV-` governance lineage.
- Require a valid human reviewer identity.
- Require a documented `PBREV-` review record and notes.
- Require review completion after all governance evidence.
- Require `APPROVED_FOR_RESEARCH_CONTINUATION`.
- Validate transition coverage, confidence, data quality, future safety, and Market Regime-before-Behaviour ordering.
- Preserve Feature Freeze and all execution locks.

This certification is research-only. It does not grant Production Certification and cannot change parameters, trading logic, positions, or send orders.

## Validation

```powershell
pytest tests/test_milestone_p_pack_9.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
