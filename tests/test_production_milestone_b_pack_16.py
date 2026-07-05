from afip.portfolio.concentration_risk import ConcentrationRisk
from afip.portfolio.exposure_limit import ExposureLimit
from afip.portfolio.portfolio_risk import PortfolioRisk
from afip.portfolio.risk_budget import RiskBudget
from afip.runtime.production_milestone_b_risk_runtime import ProductionMilestoneBRiskRuntime


def _portfolio_equity():
    return {
        "status": "PORTFOLIO_EQUITY_READY",
        "account_count": 2,
        "total_equity": 2000.0,
        "total_net_asset_value": 2200.0,
    }


def _positions():
    return (
        {"symbol": "GOLD#", "market_value": 500.0},
        {"symbol": "GOLD#", "market_value": 300.0},
        {"symbol": "GOLD#", "market_value": 200.0},
    )


def _limits():
    return {
        "maximum_risk_ratio": 0.03,
        "maximum_exposure_ratio": 0.75,
        "maximum_position_ratio": 0.55,
    }


def test_risk_budget_accepts_risk_within_equity_limit():
    result = RiskBudget().evaluate(_portfolio_equity(), proposed_risk_amount=40.0, limits=_limits())
    assert result.status == "RISK_BUDGET_READY"
    assert result.within_budget is True
    assert result.risk_ratio == 0.02


def test_risk_budget_rejects_risk_above_equity_limit():
    result = RiskBudget().evaluate(_portfolio_equity(), proposed_risk_amount=80.0, limits=_limits())
    assert result.status == "RISK_BUDGET_REVIEW"
    assert result.within_budget is False
    assert result.reason == "risk_ratio_above_limit"


def test_exposure_limit_accepts_gross_exposure_within_limit():
    result = ExposureLimit().evaluate(gross_exposure=1000.0, equity=2000.0, limits=_limits())
    assert result.status == "EXPOSURE_LIMIT_READY"
    assert result.exposure_ratio == 0.5
    assert result.within_limit is True


def test_exposure_limit_rejects_gross_exposure_above_limit():
    result = ExposureLimit().evaluate(gross_exposure=1800.0, equity=2000.0, limits=_limits())
    assert result.status == "EXPOSURE_LIMIT_REVIEW"
    assert result.within_limit is False
    assert result.reason == "exposure_ratio_above_limit"


def test_concentration_risk_accepts_balanced_position_values():
    result = ConcentrationRisk().evaluate(_positions(), _limits())
    assert result.status == "CONCENTRATION_RISK_READY"
    assert result.position_count == 3
    assert result.largest_position_ratio == 0.5


def test_concentration_risk_rejects_single_dominant_position():
    result = ConcentrationRisk().evaluate(({"market_value": 900.0}, {"market_value": 100.0}), _limits())
    assert result.status == "CONCENTRATION_RISK_REVIEW"
    assert result.within_limit is False
    assert result.reason == "largest_position_ratio_above_limit"


def test_portfolio_risk_combines_failed_rules():
    summary = PortfolioRisk().evaluate(_portfolio_equity(), 90.0, ({"market_value": 1900.0}, {"market_value": 100.0}), _limits())
    assert summary.status == "PORTFOLIO_RISK_REVIEW"
    assert summary.approved is False
    assert "risk_ratio_above_limit" in summary.failed_rules
    assert "exposure_ratio_above_limit" in summary.failed_rules
    assert "largest_position_ratio_above_limit" in summary.failed_rules


def test_production_milestone_b_risk_runtime_integrates_portfolio_risk_controls():
    result = ProductionMilestoneBRiskRuntime().run(
        portfolio_equity=_portfolio_equity(),
        proposed_risk_amount=40.0,
        positions=_positions(),
        risk_limits=_limits(),
    )
    assert result.status == "PRODUCTION_MILESTONE_B_RISK_READY"
    assert result.portfolio_risk_status == "PORTFOLIO_RISK_READY"
    assert result.risk_budget_status == "RISK_BUDGET_READY"
    assert result.exposure_status == "EXPOSURE_LIMIT_READY"
    assert result.concentration_status == "CONCENTRATION_RISK_READY"
    assert result.approved is True
    assert result.failed_rules == ()
