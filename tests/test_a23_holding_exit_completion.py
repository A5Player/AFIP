from pathlib import Path
from afip.exit_evidence_research import A23HoldingExitCompletion
from afip.historical_replay_research import AppendOnlyResearchDataset
def test_completion_waits_without_robust_blind_forward_evidence(tmp_path:Path):
 d=AppendOnlyResearchDataset(tmp_path);item=A23HoldingExitCompletion(d).certify()
 assert item.status=='WAIT' and item.production_usable is False and item.execution_authority=='NONE'
def test_completion_reports_research_evidence_without_promotion(tmp_path:Path):
 d=AppendOnlyResearchDataset(tmp_path);d.append('a22_holding_exit_validation_results',{'status':'ROBUST'})
 item=A23HoldingExitCompletion(d).certify()
 assert item.status=='RESEARCH_EVIDENCE_AVAILABLE' and item.robust_partitions==1
 assert item.automatic_promotion_allowed is False and d.verify('a23_holding_exit_certifications')
