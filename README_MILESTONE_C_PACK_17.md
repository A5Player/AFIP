# Production Milestone C Pack 17 — Decision Intelligence Enhancement

Pack 17 adds a deterministic decision enhancement layer that consumes market-regime-ready context before evaluating directional decision evidence.

## Scope

- Regime-aware decision context builder.
- Decision evidence normalization.
- Active-regime evidence aggregation before direction.
- Data-derived decision candidate ranking.
- Deterministic selection policy.
- Production runtime adapter.
- Pack validation tests.

## Quality Gates

```powershell
pytest tests/test_production_milestone_c_pack_17.py -v
pytest
python tools/afip_local_quality_check.py
```

## Architecture Notes

- Market regime classification is required before decision evaluation.
- Decision groups are filtered by active regime before direction ranking.
- Candidate scores are derived from evidence metrics, not fixed signal values.
- Runtime output is deterministic for identical regime and evidence input.
- Patch is source-only and simulation-safe.
