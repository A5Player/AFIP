from afip.cli.simulate import _display_intelligence_name


def test_financial_display_names():
    assert _display_intelligence_name("MomentumQualityIntelligence") == "MomentumIntelligence"
    assert _display_intelligence_name("LiquidityQualityIntelligence") == "LiquidityIntelligence"
    assert _display_intelligence_name("VolumeIntelligence") == "VolumeAnalysisIntelligence"
    assert _display_intelligence_name("VolatilityRiskIntelligence") == "VolatilityIntelligence"
    assert _display_intelligence_name("CorrelationIntelligence") == "CrossAssetCorrelationIntelligence"
