from afip.accounting.position_valuation import PositionValuation
from afip.accounting.unrealized_pnl import UnrealizedPnlCalculator
from afip.accounting.valuation_reconciliation import ValuationReconciliation
from afip.runtime.production_milestone_b_valuation_runtime import ProductionMilestoneBValuationRuntime


def _ledger_snapshot():
    return {
        "status": "POSITION_LEDGER_READY",
        "account_id": "ACCOUNT_A",
        "symbol": "GOLD#",
        "side": "LONG",
        "net_quantity": 0.04,
        "average_price": 2367.25,
    }


def _market_snapshot(price=2370.25):
    return {"market_price": price}


def test_position_valuation_marks_long_position_to_market():
    valuation = PositionValuation().value(_ledger_snapshot(), _market_snapshot())
    assert valuation.status == "POSITION_VALUATION_READY"
    assert valuation.account_id == "ACCOUNT_A"
    assert valuation.symbol == "GOLD#"
    assert valuation.market_price == 2370.25
    assert valuation.market_value == 94.81
    assert valuation.cost_basis == 94.69


def test_position_valuation_routes_missing_price_to_review():
    valuation = PositionValuation().value(_ledger_snapshot(), {})
    assert valuation.status == "POSITION_VALUATION_REVIEW"
    assert valuation.reason == "market_price_not_available"


def test_position_valuation_routes_unready_ledger_to_review():
    valuation = PositionValuation().value({**_ledger_snapshot(), "status": "POSITION_LEDGER_EMPTY"}, _market_snapshot())
    assert valuation.status == "POSITION_VALUATION_REVIEW"
    assert valuation.reason == "position_ledger_not_ready"


def test_unrealized_pnl_calculates_gain_for_long_position():
    valuation = PositionValuation().value(_ledger_snapshot(), _market_snapshot())
    pnl = UnrealizedPnlCalculator().calculate(valuation)
    assert pnl.status == "UNREALIZED_PNL_READY"
    assert pnl.unrealized_pnl == 0.12
    assert pnl.pnl_state == "GAIN"
    assert round(pnl.return_ratio, 6) == round(0.12 / 94.69, 6)


def test_unrealized_pnl_calculates_loss_for_long_position():
    valuation = PositionValuation().value(_ledger_snapshot(), _market_snapshot(2360.25))
    pnl = UnrealizedPnlCalculator().calculate(valuation)
    assert pnl.status == "UNREALIZED_PNL_READY"
    assert pnl.unrealized_pnl == -0.28
    assert pnl.pnl_state == "LOSS"


def test_valuation_reconciliation_accepts_return_within_limit():
    valuation = PositionValuation().value(_ledger_snapshot(), _market_snapshot())
    pnl = UnrealizedPnlCalculator().calculate(valuation)
    result = ValuationReconciliation().evaluate(valuation, pnl, {"maximum_absolute_return_ratio": 0.01})
    assert result.status == "VALUATION_RECONCILIATION_READY"
    assert result.reconciled is True
    assert result.failed_rules == ()


def test_valuation_reconciliation_rejects_return_above_limit():
    valuation = PositionValuation().value(_ledger_snapshot(), _market_snapshot(2600.00))
    pnl = UnrealizedPnlCalculator().calculate(valuation)
    result = ValuationReconciliation().evaluate(valuation, pnl, {"maximum_absolute_return_ratio": 0.01})
    assert result.status == "VALUATION_RECONCILIATION_REVIEW"
    assert result.reconciled is False
    assert "unrealized_return_limit_exceeded" in result.failed_rules


def test_production_milestone_b_valuation_runtime_integrates_valuation_and_reconciliation():
    result = ProductionMilestoneBValuationRuntime().run(
        ledger_snapshot=_ledger_snapshot(),
        market_snapshot=_market_snapshot(),
        valuation_limits={"maximum_absolute_return_ratio": 0.01},
    )
    assert result.status == "PRODUCTION_MILESTONE_B_VALUATION_READY"
    assert result.valuation_status == "POSITION_VALUATION_READY"
    assert result.pnl_status == "UNREALIZED_PNL_READY"
    assert result.reconciliation_status == "VALUATION_RECONCILIATION_READY"
    assert result.unrealized_pnl == 0.12
    assert result.failed_rules == ()
