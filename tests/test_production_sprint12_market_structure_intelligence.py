from afip.intelligence.market_structure_intelligence import MarketStructureIntelligence


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
    assert result["status"] == "READY"
    assert result["confidence"] >= 65


def test_market_structure_intelligence_handles_balanced_market():
    snapshot = {
        "highs": [10, 10.2, 10.1, 10.3, 10.2, 10.1],
        "lows": [9.7, 9.8, 9.75, 9.82, 9.78, 9.8],
        "closes": [10.0, 10.1, 10.0, 10.15, 10.05, 10.1],
    }
    result = MarketStructureIntelligence().analyze(snapshot)
    assert result["direction"] == "FLAT"
