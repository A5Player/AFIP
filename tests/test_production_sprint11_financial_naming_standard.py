from afip.standards.financial_naming_standard import find_obsolete_terms, replace_obsolete_terms


def test_financial_naming_replaces_military_terms():
    text = "DecisionIntelligence uses TrendIntelligence and PrecisionEntryIntelligence with EmergencyRiskHalt."
    updated, applied = replace_obsolete_terms(text)
    assert "DecisionIntelligence" not in updated
    assert "TrendIntelligence" not in updated
    assert "PrecisionEntryIntelligence" not in updated
    assert "EmergencyRiskHalt" not in updated
    assert "InvestmentDecisionController" in updated
    assert "TrendAllocationIntelligence" in updated
    assert "PrecisionEntryIntelligence" in updated
    assert "Emergency Risk Halt" in updated
    assert len(applied) >= 4


def test_financial_naming_scan_detects_obsolete_terms():
    found = find_obsolete_terms("MarketScannerIntelligence and MarketSession are obsolete names.")
    assert {rule.obsolete for rule in found} >= {"MarketScannerIntelligence", "MarketSession"}
