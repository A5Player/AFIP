# Production Milestone H Pack 5 — Historical Data Download and Quality Pipeline

## Scope
Pack 5 adds a deterministic historical data download and quality pipeline for VPS preparation, Walk Forward, Research, and Paper Trading readiness.

## Production Policy
- Broker: XM only.
- Symbol: GOLD# only.
- Multi broker: disabled for Version 1.
- Live execution: disabled.
- Trading logic: unchanged.

## Added Capabilities
- Historical data download plan for M1, M5, M15, H1, H4, and D1.
- Missing bar validation.
- Duplicate bar validation.
- Invalid bar validation.
- Quality score calculation.
- Walk Forward readiness gate.
- Research readiness gate.
- Paper Trading readiness gate.
- Separated Research statistics and Live statistics scopes.
- Dashboard Runtime dependency for historical download status.

## Dashboard Explainability
Every historical data step includes:
- English name.
- Thai name.
- Description.
- Waiting reason.
- Output.

## Run
```powershell
pytest tests/test_production_milestone_h_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
git add .
git commit -m "Production Milestone H Pack 5 Historical Data Download Quality Pipeline"
git push
```
