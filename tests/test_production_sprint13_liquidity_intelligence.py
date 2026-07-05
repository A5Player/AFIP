from afip.intelligence.liquidity_intelligence import LiquidityIntelligence
from afip.registry.intelligence_catalog import IntelligenceCatalog


def test_liquidity_intelligence_detects_sell_side_sweep():
    snapshot = {
        "highs": [100, 101, 101.2, 101.1, 101.3, 101.0, 101.4, 101.1, 101.2, 101.0, 101.3, 101.1],
        "lows": [98, 98.2, 98.1, 98.0, 98.2, 98.1, 98.0, 98.2, 98.1, 98.0, 97.4, 97.2],
        "closes": [99, 99.5, 99.2, 99.1, 99.4, 99.0, 99.3, 99.2, 99.1, 98.8, 98.1, 98.6],
        "spread": 20,
    }
    result = LiquidityIntelligence(equality_tolerance_points=30).analyze(snapshot)
    assert result["name"] == "LiquidityIntelligence"
    assert result["direction"] == "BUY"
    assert result["sweep_type"] == "SELL_SIDE_SWEEP"
    assert result["confidence"] >= 60


def test_liquidity_intelligence_is_registered():
    names = [module.name for module in IntelligenceCatalog().load_default()]
    assert "LiquidityIntelligence" in names
    assert "LiquidityQualityIntelligence" not in names
