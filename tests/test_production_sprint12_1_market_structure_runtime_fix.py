from afip.cli.simulate import _display_intelligence_name, _find_intelligence


def test_market_structure_safe_fallback():
    modular = {"intelligence": []}
    item = _find_intelligence(modular, "MarketStructureIntelligence")
    assert item["status"] == "INITIALIZING"
    assert item["direction"] == "NEUTRAL"


def test_financial_display_names():
    assert _display_intelligence_name("MomentumQualityIntelligence") == "MomentumIntelligence"
    assert _display_intelligence_name("LiquidityQualityIntelligence") == "LiquidityIntelligence"
    assert _display_intelligence_name("VolatilityRiskIntelligence") == "VolatilityIntelligence"
    assert _display_intelligence_name("CorrelationIntelligence") == "CrossAssetCorrelationIntelligence"
