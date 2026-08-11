import pytest
from afip.exit_evidence_research import A16ExitObservation, rank_a16_policies
def item(policy="R_STEP", realized=1.0, cost=.1): return A16ExitObservation(policy,realized,2,.5,.25,"P","PLAN","TREND","LONDON","NONE","NORMAL",cost)
def test_ranking_is_cost_aware_and_never_promotes():
    ranks=rank_a16_policies([item("A",1),item("A",1),item("B",.5),item("B",.5)],2)
    assert [x.policy_id for x in ranks]==["A","B"] and not ranks[0].production_usable
def test_incomplete_context_fails_closed():
    with pytest.raises(ValueError,match="context"): A16ExitObservation("A",1,1,1,1,"","PLAN","TREND","LONDON","NONE","NORMAL",0)
def test_insufficient_samples_are_not_ranked(): assert rank_a16_policies([item()],2)==()
