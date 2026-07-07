# Production Milestone F Pack 3 — Adaptive Confidence Engine

## Purpose

Pack 3 adds the Adaptive Confidence Engine. It converts confidence evidence into deterministic, regime-first confidence profiles before any production runtime can use adaptive confidence values.

## Production Rules

- Financial terminology only.
- Market regime is required before signal context.
- Data quality, knowledge quality, self evaluation, and stability are all evaluated before confidence adaptation is accepted.
- Runtime is deterministic.
- Production learning writes remain disabled.
- Confidence runtime writes remain disabled.

## Run

```powershell
pytest tests/test_production_milestone_f_pack_3.py -v
pytest
python tools/afip_local_quality_check.py
```
