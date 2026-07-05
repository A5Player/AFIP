from afip.intelligence.trading_cost_intelligence import TradingCostIntelligence


def test_trading_cost_intelligence_passes_normal_spread():
    result = TradingCostIntelligence().assess({"spread": 18})
    assert result["allowed"] is True
    assert result["name"] == "TradingCostIntelligence"


def test_trading_cost_intelligence_blocks_wide_spread():
    result = TradingCostIntelligence().assess({"spread": 50})
    assert result["allowed"] is False
    assert result["reason"] == "spread_above_maximum"
