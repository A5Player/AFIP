from afip.performance.benchmark_comparison import BenchmarkComparison
from afip.performance.performance_attribution import PerformanceAttribution
from afip.performance.performance_breakdown import PerformanceBreakdown
from afip.performance.performance_summary import PerformanceSummary
from afip.performance.portfolio_return import PortfolioReturn
from afip.performance.risk_adjusted_return import RiskAdjustedReturn
from afip.runtime.production_milestone_b_performance_runtime import ProductionMilestoneBPerformanceRuntime


def _portfolio_snapshot():
    return {
        "status": "PORTFOLIO_SNAPSHOT_READY",
        "opening_equity": 2000.0,
        "closing_equity": 2120.0,
        "net_profit": 120.0,
    }


def _risk_snapshot():
    return {
        "status": "PORTFOLIO_RISK_READY",
        "maximum_drawdown_ratio": 0.03,
    }


def _position_performance():
    return (
        {"account_id": "ACC1", "symbol": "GOLD#", "net_profit": 80.0},
        {"account_id": "ACC2", "symbol": "GOLD#", "net_profit": 40.0},
    )


def test_portfolio_return_calculates_return_from_equity_change():
    result = PortfolioReturn().calculate(_portfolio_snapshot())
    assert result.status == "PORTFOLIO_RETURN_READY"
    assert result.ready is True
    assert result.net_profit == 120.0
    assert result.return_ratio == 0.06
    assert result.return_percent == 6.0


def test_portfolio_return_routes_zero_opening_equity_to_review():
    result = PortfolioReturn().calculate({"status": "PORTFOLIO_SNAPSHOT_READY", "opening_equity": 0.0, "closing_equity": 100.0})
    assert result.status == "PORTFOLIO_RETURN_REVIEW"
    assert result.reason == "opening_equity_not_positive"


def test_risk_adjusted_return_calculates_return_to_drawdown_ratio():
    portfolio_return = PortfolioReturn().calculate(_portfolio_snapshot())
    result = RiskAdjustedReturn().calculate(portfolio_return, _risk_snapshot())
    assert result.status == "RISK_ADJUSTED_RETURN_READY"
    assert result.risk_adjusted_ratio == 2.0
    assert result.ready is True


def test_risk_adjusted_return_routes_missing_drawdown_to_review():
    portfolio_return = PortfolioReturn().calculate(_portfolio_snapshot())
    result = RiskAdjustedReturn().calculate(portfolio_return, {"status": "PORTFOLIO_RISK_READY", "maximum_drawdown_ratio": 0.0})
    assert result.status == "RISK_ADJUSTED_RETURN_REVIEW"
    assert result.reason == "drawdown_ratio_not_positive"


def test_performance_breakdown_calculates_position_contributions():
    result = PerformanceBreakdown().calculate(_position_performance())
    assert result.status == "PERFORMANCE_BREAKDOWN_READY"
    assert result.contribution_count == 2
    assert result.total_contribution == 120.0
    assert result.contributions[0]["contribution_percent"] == 66.6667
    assert result.contributions[1]["contribution_percent"] == 33.3333


def test_benchmark_comparison_calculates_excess_return():
    portfolio_return = PortfolioReturn().calculate(_portfolio_snapshot())
    result = BenchmarkComparison().compare(portfolio_return, benchmark_return_ratio=0.02)
    assert result.status == "BENCHMARK_COMPARISON_READY"
    assert result.excess_return_ratio == 0.04
    assert result.excess_return_percent == 4.0


def test_performance_attribution_combines_failed_rules():
    summary = PerformanceAttribution().calculate(
        {"status": "PORTFOLIO_SNAPSHOT_REVIEW", "opening_equity": 2000.0, "closing_equity": 2120.0},
        {"status": "PORTFOLIO_RISK_REVIEW", "maximum_drawdown_ratio": 0.0},
        (),
        benchmark_return_ratio=0.02,
    )
    assert summary.status == "PERFORMANCE_ATTRIBUTION_REVIEW"
    assert summary.ready is False
    assert "portfolio_return_not_ready" in summary.failed_rules
    assert "risk_adjusted_return_not_ready" in summary.failed_rules
    assert "performance_breakdown_not_ready" in summary.failed_rules
    assert "benchmark_comparison_not_ready" in summary.failed_rules


def test_production_milestone_b_performance_runtime_integrates_performance_controls():
    result = ProductionMilestoneBPerformanceRuntime().run(
        portfolio_snapshot=_portfolio_snapshot(),
        risk_snapshot=_risk_snapshot(),
        position_performance=_position_performance(),
        benchmark_return_ratio=0.02,
    )
    assert result.status == "PRODUCTION_MILESTONE_B_PERFORMANCE_READY"
    assert result.performance_attribution_status == "PERFORMANCE_ATTRIBUTION_READY"
    assert result.return_status == "PORTFOLIO_RETURN_READY"
    assert result.risk_adjusted_status == "RISK_ADJUSTED_RETURN_READY"
    assert result.breakdown_status == "PERFORMANCE_BREAKDOWN_READY"
    assert result.comparison_status == "BENCHMARK_COMPARISON_READY"
    assert result.summary_status == "PERFORMANCE_SUMMARY_READY"
    assert result.ready is True
    assert result.return_percent == 6.0
    assert result.risk_adjusted_ratio == 2.0
    assert result.excess_return_percent == 4.0
    assert result.failed_rules == ()
