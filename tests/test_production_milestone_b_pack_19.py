from afip.portfolio_analytics.allocation_efficiency import AllocationEfficiency
from afip.portfolio_analytics.analytics_summary import AnalyticsSummary
from afip.portfolio_analytics.equity_trend import EquityTrend
from afip.portfolio_analytics.portfolio_analytics import PortfolioAnalytics
from afip.portfolio_analytics.risk_efficiency import RiskEfficiency
from afip.runtime.production_milestone_b_analytics_runtime import ProductionMilestoneBAnalyticsRuntime


def _equity_observations():
    return (
        {"timestamp": "2026-07-05T00:00:00", "equity": 2000.0},
        {"timestamp": "2026-07-05T12:00:00", "equity": 2060.0},
        {"timestamp": "2026-07-06T00:00:00", "equity": 2120.0},
    )


def _performance_summary():
    return {
        "status": "PERFORMANCE_ATTRIBUTION_READY",
        "return_percent": 6.0,
    }


def _risk_snapshot():
    return {
        "status": "PORTFOLIO_RISK_READY",
        "maximum_drawdown_ratio": 0.03,
    }


def _capital_snapshot():
    return {
        "status": "CAPITAL_ALLOCATION_READY",
        "allocated_capital": 1200.0,
        "available_capital": 1800.0,
    }


def test_equity_trend_calculates_upward_trend_strength():
    result = EquityTrend().calculate(_equity_observations())
    assert result.status == "EQUITY_TREND_READY"
    assert result.ready is True
    assert result.opening_equity == 2000.0
    assert result.closing_equity == 2120.0
    assert result.equity_change == 120.0
    assert result.trend_direction == "UP"
    assert result.trend_strength_percent == 6.0


def test_equity_trend_routes_insufficient_observations_to_review():
    result = EquityTrend().calculate(({"equity": 2000.0},))
    assert result.status == "EQUITY_TREND_REVIEW"
    assert result.ready is False
    assert result.reason == "insufficient_equity_observations"


def test_risk_efficiency_calculates_return_to_drawdown_ratio():
    result = RiskEfficiency().calculate(_performance_summary(), _risk_snapshot())
    assert result.status == "RISK_EFFICIENCY_READY"
    assert result.return_percent == 6.0
    assert result.maximum_drawdown_percent == 3.0
    assert result.efficiency_ratio == 2.0


def test_risk_efficiency_routes_missing_drawdown_to_review():
    result = RiskEfficiency().calculate(_performance_summary(), {"status": "PORTFOLIO_RISK_READY", "maximum_drawdown_ratio": 0.0})
    assert result.status == "RISK_EFFICIENCY_REVIEW"
    assert result.ready is False
    assert result.reason == "drawdown_ratio_not_positive"


def test_allocation_efficiency_calculates_balanced_utilization():
    result = AllocationEfficiency().calculate(_capital_snapshot())
    assert result.status == "ALLOCATION_EFFICIENCY_READY"
    assert result.utilization_percent == 66.6667
    assert result.efficiency_status == "BALANCED"


def test_analytics_summary_combines_failed_rules():
    equity = EquityTrend().calculate(({"equity": 2000.0},))
    risk = RiskEfficiency().calculate({"status": "PERFORMANCE_ATTRIBUTION_REVIEW", "return_percent": 0.0}, _risk_snapshot())
    allocation = AllocationEfficiency().calculate({"status": "CAPITAL_ALLOCATION_REVIEW", "allocated_capital": 0.0, "available_capital": 0.0})
    result = AnalyticsSummary().summarize(equity, risk, allocation)
    assert result.status == "PORTFOLIO_ANALYTICS_REVIEW"
    assert result.ready is False
    assert "equity_trend_not_ready" in result.failed_rules
    assert "risk_efficiency_not_ready" in result.failed_rules
    assert "allocation_efficiency_not_ready" in result.failed_rules


def test_portfolio_analytics_integrates_equity_risk_and_capital_inputs():
    result = PortfolioAnalytics().calculate(_equity_observations(), _performance_summary(), _risk_snapshot(), _capital_snapshot())
    assert result.status == "PORTFOLIO_ANALYTICS_READY"
    assert result.ready is True
    assert result.equity_trend_status == "EQUITY_TREND_READY"
    assert result.risk_efficiency_status == "RISK_EFFICIENCY_READY"
    assert result.allocation_efficiency_status == "ALLOCATION_EFFICIENCY_READY"
    assert result.trend_direction == "UP"
    assert result.trend_strength_percent == 6.0
    assert result.risk_efficiency_ratio == 2.0
    assert result.capital_utilization_percent == 66.6667


def test_production_milestone_b_analytics_runtime_integrates_portfolio_analytics():
    result = ProductionMilestoneBAnalyticsRuntime().run(_equity_observations(), _performance_summary(), _risk_snapshot(), _capital_snapshot())
    assert result.status == "PRODUCTION_MILESTONE_B_ANALYTICS_READY"
    assert result.portfolio_analytics_status == "PORTFOLIO_ANALYTICS_READY"
    assert result.ready is True
    assert result.equity_trend_status == "EQUITY_TREND_READY"
    assert result.risk_efficiency_status == "RISK_EFFICIENCY_READY"
    assert result.allocation_efficiency_status == "ALLOCATION_EFFICIENCY_READY"
    assert result.trend_direction == "UP"
    assert result.trend_strength_percent == 6.0
    assert result.risk_efficiency_ratio == 2.0
    assert result.capital_utilization_percent == 66.6667
    assert result.failed_rules == ()
