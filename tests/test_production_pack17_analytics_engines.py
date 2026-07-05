from afip.analytics.equity_curve_engine import EquityCurveEngine
from afip.analytics.market_session_engine import MarketSessionEngine
from afip.analytics.performance_metrics_engine import PerformanceMetricsEngine
from afip.analytics.time_window_analytics_engine import TimeWindowAnalyticsEngine
from afip.analytics.trade_distribution_engine import TradeDistributionEngine


def sample_trades():
    return [
        {"symbol": "GOLD#", "action": "BUY", "session": "US", "weekday": "MON", "hour": 14, "profit": 12.0},
        {"symbol": "GOLD#", "action": "BUY", "session": "US", "weekday": "MON", "hour": 14, "profit": -4.0},
        {"symbol": "GOLD#", "action": "SELL", "session": "ASIA", "weekday": "TUE", "hour": 2, "profit": 8.0},
    ]


def test_performance_metrics_engine_calculates_profit_factor():
    result = PerformanceMetricsEngine().evaluate(sample_trades())
    assert result["status"] == "READY"
    assert result["total_trades"] == 3
    assert result["net_profit"] == 16.0
    assert result["profit_factor"] == 5.0


def test_equity_curve_engine_calculates_drawdown():
    result = EquityCurveEngine().evaluate([100.0, 120.0, 110.0, 130.0])
    assert result["status"] == "READY"
    assert result["end_equity"] == 130.0
    assert result["max_drawdown"] == 10.0


def test_trade_distribution_engine_builds_buckets():
    result = TradeDistributionEngine().evaluate(sample_trades())
    assert result["status"] == "READY"
    assert result["bucket_count"] == 2
    assert result["largest_bucket"] == "GOLD#:BUY:US"


def test_time_window_analytics_engine_ranks_windows():
    result = TimeWindowAnalyticsEngine().evaluate(sample_trades())
    assert result["status"] == "READY"
    assert result["top_windows"][0]["window"] in {"MON:14", "TUE:02"}


def test_market_session_engine_classifies_overlap():
    result = MarketSessionEngine().evaluate(13)
    assert result["session"] == "US_EUROPE_OVERLAP"
