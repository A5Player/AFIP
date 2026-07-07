# Production Milestone F Pack 2 - Self Evaluation Engine

## Purpose
Pack 2 adds a deterministic self evaluation layer for closed decision observations. The layer reviews decision quality by market regime before accepting any adaptive learning evidence.

## Production Rules
- Market regime is required before outcome review.
- Closed decision evidence is grouped by market regime and decision status.
- Confidence alignment, data quality, knowledge quality, and realized outcome are evaluated deterministically.
- Production learning is not updated directly from this pack.
- Review-required profiles are surfaced before later adaptive components consume the evidence.

## Runtime
Use:

```python
from afip.runtime.production_milestone_f_self_evaluation_runtime import run_production_milestone_f_self_evaluation
```

## Validation
```powershell
pytest tests/test_production_milestone_f_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
```
