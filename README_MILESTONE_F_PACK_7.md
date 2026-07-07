# Production Milestone F Pack 7 - AI Integration

Patch-only production update for deterministic AI integration planning.

## Scope

- Adds `afip.ai_integration` package.
- Adds a production runtime entrypoint for Pack 7.
- Converts runtime adaptation evidence into regime-first AI assist profiles.
- Keeps all AI output observation/planning only; no autonomous execution and no runtime writes.
- Preserves financial terminology and backward compatibility.

## Validation

```powershell
pytest tests/test_production_milestone_f_pack_7.py -v
pytest
python tools/afip_local_quality_check.py
```
