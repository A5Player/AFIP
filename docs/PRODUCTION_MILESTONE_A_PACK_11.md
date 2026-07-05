# Production Milestone A Pack 11 — Adaptive Optimization

Pack 11 extends Production Milestone A with adaptive optimization designed for production readiness and CI stability.

## A1 Adaptive Intelligence Core

`AdaptiveParameterCalibration` converts regime quality, execution quality, learning quality, volatility pressure, and drawdown pressure into calibrated production parameters.

Outputs:

- entry threshold
- exit threshold
- allocation multiplier
- confidence floor
- calibration status
- reason code

## A2 Market Regime Intelligence

The calibration process considers market pressure through volatility and drawdown metrics. This keeps allocation conservative during unstable market conditions while allowing higher allocation during higher-quality regimes.

## A3 Learning & Optimization

`LearningQualityEvaluation` checks whether learning metrics are mature enough for parameter optimization.

Learning quality inputs:

- sample count
- win rate
- profit factor
- drawdown ratio
- drift ratio

Optimization status values:

- `OPTIMIZATION_READY`
- `OPTIMIZATION_LIMITED`
- `OBSERVATION_ONLY`

## A4 Runtime Integration

`ProductionMilestoneAOptimizationRuntime` integrates calibration, confidence scaling, and learning quality into one deterministic runtime result.

Runtime actions:

- `APPLY_CALIBRATED_PARAMETERS`
- `MAINTAIN_CURRENT_PARAMETERS`
- `REDUCE_ALLOCATION_PARAMETERS`
- `NO_PARAMETER_CHANGE`

## Compatibility

Pack 11 is additive. It does not change existing Pack 1–10 imports, runtime behavior, simulation output, or MT5 check behavior.

## Quality Requirements

- Implementation included
- Pytest included
- Documentation included
- Local quality compatible
- GitHub CI compatible
- International financial terminology only
