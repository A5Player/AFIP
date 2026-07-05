from afip.intelligence.market_structure_intelligence import MarketStructureIntelligence
from afip.registry.intelligence_catalog import IntelligenceCatalog


def test_market_structure_intelligence_detects_bullish_structure():
    snapshot = {
        "highs": [10, 12, 11, 13, 12, 15, 14, 16, 15, 18, 17, 19],
        "lows": [8, 9, 8.5, 10, 9.5, 11, 10.5, 12, 11.5, 13, 12.5, 14],
        "closes": [9, 11, 10, 12, 11, 14, 13, 15, 14, 17, 16, 20],
        "spread": 20,
    }
    result = MarketStructureIntelligence().analyze(snapshot)
    assert result["name"] == "MarketStructureIntelligence"
    assert result["direction"] == "BUY"
    assert result["confidence"] >= 70
    assert result["status"] in {"READY", "CAUTION"}


def test_market_structure_intelligence_is_registered():
    names = [module.name for module in IntelligenceCatalog().load_default()]
    assert "MarketStructureIntelligence" in names
