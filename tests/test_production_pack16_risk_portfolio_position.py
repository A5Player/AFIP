from afip.engine.adaptive_risk_engine import AdaptiveRiskEngine
from afip.engine.drawdown_engine import DrawdownEngine
from afip.engine.exposure_engine import ExposureEngine
from afip.engine.portfolio_engine import PortfolioEngine
from afip.engine.position_engine import PositionEngine
from afip.engine.trade_lifecycle_engine import TradeLifecycleEngine


def test_adaptive_risk_engine_blocks_high_spread():
    result = AdaptiveRiskEngine().evaluate({"decision_confidence": 85, "drawdown_percent": 2, "spread_usage": 1.05})
    assert result["action"] == "WAIT"
    assert result["risk_tier"] == "RISK_OFF"


def test_position_engine_calculates_minimum_lot():
    result = PositionEngine().evaluate({"equity": 1000, "risk_percent": 1, "stop_points": 900, "point_value_per_lot": 1})
    assert result["status"] == "READY"
    assert result["suggested_lot"] >= 0.01


def test_exposure_engine_blocks_excess_exposure():
    result = ExposureEngine(max_exposure_percent=20).evaluate({"equity": 1000, "open_exposure": 250})
    assert result["status"] == "BLOCKED"
    assert result["action"] == "WAIT"


def test_drawdown_engine_warns_near_limit():
    result = DrawdownEngine(max_drawdown_percent=10).evaluate({"balance": 1000, "equity": 920})
    assert result["status"] == "CAUTION"
    assert result["action"] == "REDUCE_RISK"


def test_portfolio_engine_aggregates_accounts():
    result = PortfolioEngine().evaluate({"accounts": [
        {"balance": 500, "equity": 510, "open_positions": 1},
        {"balance": 500, "equity": 490, "open_positions": 0},
    ]})
    assert result["status"] == "READY"
    assert result["account_count"] == 2
    assert result["total_balance"] == 1000


def test_trade_lifecycle_engine_protects_giveback():
    result = TradeLifecycleEngine().evaluate({"floating_profit": 50, "peak_profit": 120, "position_confidence": 62})
    assert result["action"] == "PROTECT_PROFIT"
    assert result["lifecycle_state"] == "PROFIT_PROTECTION"
