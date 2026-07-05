# Production Milestone B Pack 6 — Market Context Engine

## Objective

Production Milestone B Pack 6 adds a market context layer for AFIP runtime decisions. The pack is additive, CI compatible, and preserves backward compatibility with the existing simulation and modular intelligence runtime.

## Components

- `MarketStateClassifier` — classifies `TRENDING`, `SIDEWAYS`, `BREAKOUT`, `PULLBACK`, or `NEUTRAL` market state.
- `VolatilityContext` — classifies volatility and produces an execution quality adjustment factor.
- `LiquidityContext` — classifies liquidity expansion, contraction, or balanced liquidity.
- `ContextTransitionModel` — evaluates market context stability across state changes.
- `MarketContextEngine` — combines state, volatility, liquidity, and transition context into a unified context score.
- `ProductionMilestoneBContextRuntime` — serializable runtime adapter for production validation and CI.

## Runtime Flow

```text
Market Metrics
  -> Market Context
  -> Intelligence Fusion
  -> Adaptive Weighting
  -> Conflict Resolution
  -> Unified Decision
  -> Execution Planning
```

## Production Compatibility

- No existing command line interface is modified.
- No existing module is removed.
- No trading execution behavior is changed.
- Output is deterministic and serializable.
- Terminology follows international financial language.

## Validation

```powershell
pytest tests/test_production_milestone_b_pack_6.py
python tools/afip_local_quality_check.py
```
