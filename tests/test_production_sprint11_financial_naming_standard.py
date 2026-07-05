from afip.standards.financial_naming_standard import find_obsolete_terms, replace_obsolete_terms


def test_financial_naming_keeps_approved_financial_terms():
    text = "DecisionIntelligence uses TrendIntelligence and PrecisionEntryIntelligence."
    updated, applied = replace_obsolete_terms(text)
    assert updated == text
    assert applied == []


def test_financial_naming_detects_prohibited_military_terms():
    found = find_obsolete_terms("Commander and Sniper are prohibited legacy terms.")
    assert {rule.obsolete for rule in found} >= {"Commander", "Sniper"}
