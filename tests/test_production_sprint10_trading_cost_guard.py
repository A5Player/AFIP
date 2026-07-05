from afip.intelligence.trading_cost_intelligence import TradingCostIntelligence
from afip.market.mt5_market_data_provider import MT5MarketDataProvider


def test_trading_cost_intelligence_passes_normal_gold_spread():
    validation_intelligence = TradingCostIntelligence()
    result = validation_intelligence.assess({"spread": 18})
    assert result["status"] == "PASS"
    assert result["allowed"] is True


def test_trading_cost_intelligence_blocks_wide_gold_spread():
    validation_intelligence = TradingCostIntelligence()
    result = validation_intelligence.assess({"spread": 50})
    assert result["status"] == "BLOCK"
    assert result["allowed"] is False
    assert result["reason"] == "spread_above_maximum"


def test_mt5_provider_converts_gold_price_spread_to_points():
    spread = MT5MarketDataProvider._spread_points(2400.10, 2400.41, point_size=0.01)
    assert spread == 31.0
