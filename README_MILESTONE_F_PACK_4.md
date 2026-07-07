# Production Milestone F Pack 4 — Experience Knowledge Engine

## Purpose

Pack 4 adds the Experience Knowledge Engine. It converts closed market experience into deterministic, regime-first knowledge profiles before any production runtime can use experience evidence.

## Production Rules

- Financial terminology only.
- Market regime is required before signal context.
- Closed experience is evaluated with adaptive confidence, self evaluation, data quality, knowledge quality, recency, and realized result.
- Runtime is deterministic.
- Experience runtime writes remain disabled.
- Production learning writes remain disabled.

## Run

```powershell
pytest tests/test_production_milestone_f_pack_4.py -v
pytest
python tools/afip_local_quality_check.py
```
