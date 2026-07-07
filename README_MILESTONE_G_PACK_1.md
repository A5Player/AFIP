# Production Milestone G Pack 1 - Runtime Observability Foundation

This patch adds a compact runtime observability layer for AFIP production hardening.

## Scope

- Runtime metrics observation contract
- Deterministic observability scoring
- Runtime explainability report
- In-memory observability repository
- Runtime facade and production entry point
- Pack-specific tests and run scripts

## Production Rules

- Patch only
- Financial terminology only
- No unrelated refactor
- Deterministic runtime
- Market regime before signal context
- Knowledge-first and data-first compatible
- No AI layer expansion

## Validation

```powershell
pytest tests/test_production_milestone_g_pack_1.py -v
pytest
python tools/afip_local_quality_check.py
```
