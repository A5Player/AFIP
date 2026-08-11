import pytest
from afip.exit_evidence_research import outcome_to_a16_evidence
from afip.exit_outcome_research import A16ResearchContext

def context(): return A16ResearchContext("P","FAMILY","PLAN","2026-01-01T00:00:00Z","TREND","LONDON","OPEN","NONE","NORMAL","VERIFIED")
def outcome(**more):
    base={"policy_id":"R_STEP","realized_r":1.0,"maximum_favorable_excursion_r":2.0,"maximum_adverse_excursion_r":.5,"research_state":"EXPERIMENTAL","production_usable":False}; base.update(more); return base
def test_bridge_preserves_context_and_calculates_giveback():
    item=outcome_to_a16_evidence(outcome=outcome(),context=context(),execution_cost_r=.1)
    assert item.session_name=="LONDON" and item.giveback_r==1.0 and item.execution_cost_r==.1
def test_bridge_rejects_production_outcome():
    with pytest.raises(ValueError,match="experimental"): outcome_to_a16_evidence(outcome=outcome(production_usable=True),context=context(),execution_cost_r=0)
def test_bridge_rejects_missing_outcome_metric():
    data=outcome(); del data["realized_r"]
    with pytest.raises(ValueError,match="incomplete"): outcome_to_a16_evidence(outcome=data,context=context(),execution_cost_r=0)
