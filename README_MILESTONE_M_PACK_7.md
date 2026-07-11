# Milestone M Pack 7 — Pattern Explainability

Adds deterministic, research-only explanations for validated and rejected Pattern and Cluster scopes.

## Capabilities
- Auditable primary and supporting reasons
- Explicit risk notes
- Stable feature-contribution ordering
- Market Regime and lineage preservation
- Full explanation coverage reporting
- Future-leakage, data-quality, broker, symbol, base-unit, and execution-lock controls
- Bilingual dashboard panel

Production knowledge approval remains disabled. No broker request or order transmission is created.

## Validation
```powershell
pytest tests/test_milestone_m_pack_7.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git
```powershell
git add .
git commit -m "Milestone M Pack 7 Pattern Explainability"
git push
```
