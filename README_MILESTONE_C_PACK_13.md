# Production Milestone C Pack 13 — Adaptive Parameter Foundation

Pack 13 adds the first adaptive parameter foundation for AFIP Production Milestone C.

## Scope

- Regime-first parameter observation model
- Adaptive parameter repository
- Stop distance, profit objective, holding period, and confidence floor candidates
- Cost-aware parameter quality assessment
- Deterministic adaptive parameter runtime
- Production runtime entrypoint

## Production Rules

- Financial terminology only
- Market regime before signal
- Data-first architecture
- Knowledge-first architecture
- Deterministic runtime
- Patch-only delivery

## Test Command

```powershell
pytest tests/test_production_milestone_c_pack_13.py -v
```

## Full Quality Command

```powershell
python tools/afip_local_quality_check.py
```
