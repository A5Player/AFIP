# Production Milestone G Pack 6 — Paper Trading Framework

Pack 6 adds a deterministic paper trading readiness layer. It evaluates simulated trading records, confirms the runtime remains simulation-only, and produces a paper trading report without creating live orders or changing trading decisions.

## Scope

- Paper trading observation normalization
- Paper trading policy gate
- Paper trading profile and report
- In-memory paper trading repository
- Runtime entry point
- Pack-specific tests
- Updated AFIP project database and handoff

## Validation

```powershell
pytest tests/test_production_milestone_g_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
```
