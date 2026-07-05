# AFIP Production Milestone A

## Scope
Production Milestone A adds an additive adaptive intelligence layer after Production Pack 18. It is designed for production readiness, backward compatibility and GitHub CI compatibility.

## Components

### A1 Adaptive Intelligence Core
File: `afip/intelligence/adaptive_intelligence_core.py`

- Normalizes existing dict-style intelligence outputs and new dataclass signals.
- Aggregates BUY, SELL and HOLD scores with confidence, weight and readiness handling.
- Returns a stable dictionary contract through `AdaptiveDecision.to_dict()`.

### A2 Market Regime Intelligence
File: `afip/intelligence/market_regime_intelligence_v2.py`

- Classifies market state as `TRENDING`, `RANGING`, `VOLATILE`, `LOW_LIQUIDITY` or `TRANSITION`.
- Produces action bias, risk adjustment and entry threshold adjustment.
- Keeps execution-safe HOLD behavior when liquidity or spread quality is poor.

### A3 Learning and Optimization
File: `afip/learning/adaptive_learning_optimizer.py`

- Uses historical outcome samples to propose bounded parameter adjustments.
- Requires at least five samples before returning `READY`.
- Does not place orders and does not bypass production gates.

### A4 Runtime Integration
File: `afip/runtime/production_milestone_a_runtime.py`

- Coordinates A1, A2 and A3 into one production-safe runtime output.
- Returns `production_allowed=false` if any layer requires observation.
- Preserves existing runtime compatibility by accepting plain dictionaries.

## Safety Rules

- No direct order execution is included in Milestone A.
- Learning output is advisory and bounded.
- Market regime HOLD bias blocks production action.
- Adaptive confidence must meet the learning entry threshold.

## Local Quality

Run:

```powershell
pytest tests/test_production_milestone_a.py
python tools/validate_financial_naming.py
python tools/afip_local_quality_check.py
```

The new files use international financial terminology only and avoid non-financial naming.

## GitHub CI

The tests are standard pytest tests with no external dependency. They are compatible with the existing CI pattern that already runs the test suite.
