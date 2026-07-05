# AFIP Phase 27 — Strategy Layer

Adds strategy modules:
- TrendFollowingStrategy
- BreakoutStrategy
- MeanReversionStrategy
- StrategyAggregator
- StrategySignalWorkflow

Safety:
- SIMULATION only
- No live order execution

Next:
Phase 28 should add a backtest runner that feeds candle data through strategy and signal workflows.
