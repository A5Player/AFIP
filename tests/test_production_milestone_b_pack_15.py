from afip.portfolio.equity_calculator import EquityCalculator
from afip.portfolio.equity_reconciliation import EquityReconciliation
from afip.portfolio.net_asset_value import NetAssetValueCalculator
from afip.portfolio.portfolio_equity import PortfolioEquity
from afip.runtime.production_milestone_b_equity_runtime import ProductionMilestoneBEquityRuntime


def _account_snapshot():
    return {
        "account_id": "ACCOUNT_A",
        "balance": 1000.0,
        "realized_pnl": 25.0,
        "unrealized_pnl": 12.5,
    }


def test_equity_calculator_builds_ready_equity_snapshot():
    snapshot = EquityCalculator().calculate(_account_snapshot())
    assert snapshot.status == "EQUITY_READY"
    assert snapshot.account_id == "ACCOUNT_A"
    assert snapshot.balance == 1000.0
    assert snapshot.realized_pnl == 25.0
    assert snapshot.unrealized_pnl == 12.5
    assert snapshot.equity == 1037.5


def test_equity_calculator_routes_negative_balance_to_review():
    snapshot = EquityCalculator().calculate({**_account_snapshot(), "balance": -1.0})
    assert snapshot.status == "EQUITY_REVIEW"
    assert snapshot.reason == "negative_balance_not_allowed"


def test_net_asset_value_calculator_adds_position_value_to_equity():
    equity = EquityCalculator().calculate(_account_snapshot())
    nav = NetAssetValueCalculator().calculate(equity, position_value=94.81)
    assert nav.status == "NET_ASSET_VALUE_READY"
    assert nav.equity == 1037.5
    assert nav.invested_value == 94.81
    assert nav.net_asset_value == 1132.31


def test_net_asset_value_calculator_routes_unready_equity_to_review():
    equity = EquityCalculator().calculate({**_account_snapshot(), "balance": -1.0})
    nav = NetAssetValueCalculator().calculate(equity, position_value=94.81)
    assert nav.status == "NET_ASSET_VALUE_REVIEW"
    assert nav.reason == "equity_snapshot_not_ready"


def test_portfolio_equity_summarizes_multiple_accounts():
    first = EquityCalculator().calculate(_account_snapshot())
    second = EquityCalculator().calculate({**_account_snapshot(), "account_id": "ACCOUNT_B", "balance": 500.0, "realized_pnl": 5.0, "unrealized_pnl": -2.0})
    summary = PortfolioEquity().summarize([first, second])
    assert summary.status == "PORTFOLIO_EQUITY_READY"
    assert summary.account_count == 2
    assert summary.total_balance == 1500.0
    assert summary.total_realized_pnl == 30.0
    assert summary.total_unrealized_pnl == 10.5
    assert summary.total_equity == 1540.5


def test_equity_reconciliation_accepts_equity_above_minimum():
    equity = EquityCalculator().calculate(_account_snapshot())
    nav = NetAssetValueCalculator().calculate(equity, position_value=94.81)
    result = EquityReconciliation().evaluate(equity, nav, {"minimum_equity": 500.0, "maximum_nav_to_equity_ratio": 2.0})
    assert result.status == "EQUITY_RECONCILIATION_READY"
    assert result.reconciled is True
    assert result.failed_rules == ()


def test_equity_reconciliation_rejects_equity_below_minimum():
    equity = EquityCalculator().calculate(_account_snapshot())
    nav = NetAssetValueCalculator().calculate(equity, position_value=94.81)
    result = EquityReconciliation().evaluate(equity, nav, {"minimum_equity": 2000.0})
    assert result.status == "EQUITY_RECONCILIATION_REVIEW"
    assert result.reconciled is False
    assert "minimum_equity_not_met" in result.failed_rules


def test_production_milestone_b_equity_runtime_integrates_equity_nav_and_reconciliation():
    result = ProductionMilestoneBEquityRuntime().run(
        account_snapshot=_account_snapshot(),
        position_value=94.81,
        equity_limits={"minimum_equity": 500.0, "maximum_nav_to_equity_ratio": 2.0},
    )
    assert result.status == "PRODUCTION_MILESTONE_B_EQUITY_READY"
    assert result.equity_status == "EQUITY_READY"
    assert result.nav_status == "NET_ASSET_VALUE_READY"
    assert result.portfolio_status == "PORTFOLIO_EQUITY_READY"
    assert result.reconciliation_status == "EQUITY_RECONCILIATION_READY"
    assert result.net_asset_value == 1132.31
    assert result.failed_rules == ()
