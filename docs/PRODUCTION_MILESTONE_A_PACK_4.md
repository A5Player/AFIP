# AFIP Production Milestone A Pack 4

Pack 4 extends the additive Milestone A production layer with final production controls for adaptive runtime usage.

## Scope

- A1 Adaptive Intelligence Core
  - `SignalQualityAuditor` validates adaptive signal quality, side consistency, and minimum confidence.
- A2 Market Regime Intelligence
  - `RegimeRiskBudget` maps market regime, exposure control, and stability into a conservative risk budget.
- A3 Learning & Optimization
  - `OptimizationParameterGovernor` bounds adaptive parameter changes for production safety.
- A4 Runtime Integration
  - `ProductionMilestoneAProductionControl` combines Pack 1-3 decision bridge output with Pack 4 audit, risk budget, and optimization governance.

## Production Rules

- Additive only: no existing runtime contract is removed or renamed.
- Backward compatible: Pack 4 consumes current dictionaries and existing adaptive signal objects.
- International financial terminology only.
- Protective default: any missing or low-quality input returns `OBSERVE` and `HOLD`.
- CI compatible: pytest-only validation, no broker connection required.

## Validation

Run:

```powershell
pytest tests/test_production_milestone_a.py tests/test_production_milestone_a_pack_2.py tests/test_production_milestone_a_pack_3.py tests/test_production_milestone_a_pack_4.py
python tools/afip_local_quality_check.py
```

Expected focused Pack 1-4 result: `32 passed`.
