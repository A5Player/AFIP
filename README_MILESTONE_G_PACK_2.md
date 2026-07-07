# Production Milestone G Pack 2 - Production Event Log

Pack 2 adds a compact production event log and configuration version evidence layer.
It does not add a new AI decision layer, does not change execution behavior, and does
not write runtime configuration automatically.

## Purpose

- Preserve a deterministic event trail for runtime decisions.
- Keep Market Regime before Signal Context in every event record.
- Track configuration version evidence for review and rollback readiness.
- Support explainable audit reports without changing production decisions.

## Validation

```powershell
pytest tests/test_production_milestone_g_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
```
