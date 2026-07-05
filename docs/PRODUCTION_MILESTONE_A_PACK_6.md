# AFIP Production Milestone A Pack 6

Pack 6 extends Milestone A with maturity-aware production intelligence.
It is additive, backward compatible, and uses international financial terminology only.

## Scope

- A1: Portfolio Maturity Index
- A2: Market Regime Consistency Index
- A3: Optimization Drift Index
- A4: Production Milestone A Maturity Runtime

## Production Components

| Area | File | Purpose |
|---|---|---|
| A1 | `afip/intelligence/portfolio_maturity_index.py` | Evaluates capital efficiency, drawdown quality, and exposure balance. |
| A2 | `afip/intelligence/market_regime_consistency_index.py` | Measures regime stability across recent market observations. |
| A3 | `afip/learning/optimization_drift_index.py` | Keeps adaptive parameters within production-safe ranges. |
| A4 | `afip/runtime/production_milestone_a_maturity_runtime.py` | Combines portfolio runtime, maturity, regime consistency, and optimization drift. |

## Validation

```powershell
pytest tests/test_production_milestone_a_pack_6.py
python tools/afip_local_quality_check.py
```

## Compatibility

Pack 6 does not alter existing public contracts from Pack 1 to Pack 5.
It only adds new modules, tests, and documentation.
