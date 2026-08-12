from afip.exit_evidence_research import A16ExitObservation, A16ResearchCompletion
from afip.historical_replay_research import AppendOnlyResearchDataset

def observation(index): return A16ExitObservation("R_STEP",1,2,.5,.2,f"P{index}","PLAN","TREND","LONDON","NONE","NORMAL",.1)
def test_completion_persists_append_only_evidence_and_ranking(tmp_path):
    store=AppendOnlyResearchDataset(tmp_path / "runtime" / "research")
    report, cert=A16ResearchCompletion(store,2).record_and_report([observation(1),observation(2)])
    assert report.status=="READY" and cert.append_only_verified and cert.execution_authority=="NONE"
    assert store.count("a16_exit_evidence_observations")==2 and store.count("a16_exit_policy_rankings")==1
def test_completion_wait_is_valid_no_trade_research_outcome(tmp_path):
    report, cert=A16ResearchCompletion(AppendOnlyResearchDataset(tmp_path),2).record_and_report([observation(1)])
    assert report.status=="WAIT" and cert.reason=="minimum_research_sample_not_met"
