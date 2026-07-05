from afip.portfolio.production_portfolio import ProductionPortfolio
from afip.runtime.production_milestone_b_portfolio_runtime import ProductionMilestoneBPortfolioRuntime


def _accounts():
    return (
        {"account_id": "ACC-01", "balance": 1000.0, "realized_pnl": 50.0, "unrealized_pnl": 25.0},
        {"account_id": "ACC-02", "balance": 1500.0, "realized_pnl": 25.0, "unrealized_pnl": 0.0},
    )


def _positions():
    return (
        {"symbol": "XAUUSD", "market_value": 300.0},
        {"symbol": "EURUSD", "market_value": 200.0},
    )


def _requests():
    return (
        {"symbol": "XAUUSD", "requested_capital": 200.0},
        {"symbol": "EURUSD", "requested_capital": 100.0},
    )


def _policy():
    return {
        "maximum_risk_ratio": 0.05,
        "maximum_exposure_ratio": 0.5,
        "maximum_position_ratio": 0.7,
        "reserve_ratio": 0.2,
        "maximum_allocation_ratio": 0.5,
        "maximum_utilization_ratio": 0.8,
    }


def _equity_observations():
    return (
        {"timestamp": "2026-07-05T00:00:00", "equity": 2500.0},
        {"timestamp": "2026-07-05T12:00:00", "equity": 2550.0},
        {"timestamp": "2026-07-06T00:00:00", "equity": 2600.0},
    )


def test_production_portfolio_builds_ready_integrated_state():
    result = ProductionPortfolio().build(_accounts(), _positions(), 100.0, 300.0, _requests(), _equity_observations(), _policy())
    assert result.status == "PRODUCTION_PORTFOLIO_READY"
    assert result.ready is True
    assert result.equity_status == "PORTFOLIO_EQUITY_READY"
    assert result.risk_status == "PORTFOLIO_RISK_READY"
    assert result.capital_status == "CAPITAL_ALLOCATION_READY"
    assert result.analytics_status == "PORTFOLIO_ANALYTICS_READY"
    assert result.account_count == 2
    assert result.position_count == 2
    assert result.total_balance == 2500.0
    assert result.total_equity == 2600.0
    assert result.gross_exposure == 500.0
    assert result.trend_direction == "UP"
    assert result.failed_rules == ()


def test_production_portfolio_routes_missing_accounts_to_review():
    result = ProductionPortfolio().build((), _positions(), 100.0, 300.0, _requests(), _equity_observations(), _policy())
    assert result.status == "PRODUCTION_PORTFOLIO_REVIEW"
    assert result.ready is False
    assert "portfolio_equity_not_ready" in result.failed_rules


def test_production_portfolio_routes_excessive_risk_to_review():
    result = ProductionPortfolio().build(_accounts(), _positions(), 500.0, 300.0, _requests(), _equity_observations(), _policy())
    assert result.status == "PRODUCTION_PORTFOLIO_REVIEW"
    assert result.ready is False
    assert "risk_ratio_above_limit" in result.failed_rules


def test_production_portfolio_routes_excessive_allocation_to_review():
    result = ProductionPortfolio().build(_accounts(), _positions(), 100.0, 2000.0, _requests(), _equity_observations(), _policy())
    assert result.status == "PRODUCTION_PORTFOLIO_REVIEW"
    assert result.ready is False
    assert "allocation_ratio_above_limit" in result.failed_rules


def test_production_portfolio_runtime_integrates_pack_20_state():
    result = ProductionMilestoneBPortfolioRuntime().run(_accounts(), _positions(), 100.0, 300.0, _requests(), _equity_observations(), _policy())
    assert result.status == "PRODUCTION_MILESTONE_B_PORTFOLIO_READY"
    assert result.portfolio_status == "PRODUCTION_PORTFOLIO_READY"
    assert result.ready is True
    assert result.equity_status == "PORTFOLIO_EQUITY_READY"
    assert result.risk_status == "PORTFOLIO_RISK_READY"
    assert result.capital_status == "CAPITAL_ALLOCATION_READY"
    assert result.analytics_status == "PORTFOLIO_ANALYTICS_READY"
    assert result.total_equity == 2600.0
    assert result.available_capital == 2080.0
    assert result.failed_rules == ()


def test_production_portfolio_runtime_run_dict_is_deterministic():
    result = ProductionMilestoneBPortfolioRuntime().run_dict(_accounts(), _positions(), 100.0, 300.0, _requests(), _equity_observations(), _policy())
    assert result["status"] == "PRODUCTION_MILESTONE_B_PORTFOLIO_READY"
    assert result["portfolio_status"] == "PRODUCTION_PORTFOLIO_READY"
    assert result["account_count"] == 2
    assert result["position_count"] == 2
    assert result["failed_rules"] == ()


def test_production_portfolio_runtime_uses_generated_equity_observations_when_missing():
    result = ProductionMilestoneBPortfolioRuntime().run(_accounts(), _positions(), 100.0, 300.0, _requests(), runtime_policy=_policy())
    assert result.status == "PRODUCTION_MILESTONE_B_PORTFOLIO_READY"
    assert result.trend_direction == "UP"
    assert result.trend_strength_percent == 4.0


def test_production_portfolio_runtime_preserves_financial_metrics_on_review():
    policy = dict(_policy(), maximum_exposure_ratio=0.05)
    result = ProductionMilestoneBPortfolioRuntime().run(_accounts(), _positions(), 100.0, 300.0, _requests(), _equity_observations(), policy)
    assert result.status == "PRODUCTION_MILESTONE_B_PORTFOLIO_REVIEW"
    assert result.ready is False
    assert result.total_equity == 2600.0
    assert result.gross_exposure == 500.0
    assert "exposure_ratio_above_limit" in result.failed_rules
