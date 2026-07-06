# Production Milestone E Pack 4 — Confidence Calibration

## Purpose

Adds confidence calibration intelligence to compare raw confidence with realized accuracy after market regime is known.

## Production Rules

- Market regime is normalized before confidence bucket selection.
- Calibration uses data-derived observations only.
- Runtime remains deterministic.
- Traceability is required for usable observations.
- High calibration error and high confidence drift block readiness.

## Validation

Run:

```powershell
pytest tests/test_production_milestone_e_pack_4.py -v
pytest
python tools/afip_local_quality_check.py
```
