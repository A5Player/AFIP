# Production Milestone C Pack 16 — Market Regime Intelligence

Pack 16 adds a deterministic market-regime intelligence layer that classifies the current market state before any directional signal is evaluated.

## Scope

- Regime evidence normalization.
- Market-regime-first profile repository.
- Learned regime threshold generation from evidence.
- Current market regime classification.
- Production runtime adapter.
- Pack validation tests.

## Quality Gates

```powershell
pytest tests/test_production_milestone_c_pack_16.py -v
pytest
python tools/afip_local_quality_check.py
```

## Architecture Notes

- Market regime is evaluated before signal direction.
- Thresholds are derived from observations, not fixed signal constants.
- Runtime output is deterministic for identical evidence and snapshot input.
- Patch is source-only and simulation-safe.
