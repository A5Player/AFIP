# AFIP Production Pack 17 - Analytics, Backtest Metrics, and Runtime Reporting

Production Pack 17 adds production analytics components that evaluate closed-trade performance, equity stability, time windows, distribution buckets, walk-forward validation, scenario stress results, and compact runtime reporting.

## Added Components

- PerformanceMetricsEngine
- EquityCurveEngine
- TradeDistributionEngine
- TimeWindowAnalyticsEngine
- MarketSessionEngine
- BacktestMetricsEngine
- WalkForwardEngine
- ScenarioStressEngine
- AnalyticsReportBuilder
- RuntimeStatusReport

## Validation

Run:

```powershell
python -m pytest
python tools/afip_local_quality_check.py
python afip.py simulate
```

## Compatibility

This pack is additive. It does not remove or reduce existing runtime, MT5, institutional intelligence, decision, portfolio, risk, or reporting functionality.
