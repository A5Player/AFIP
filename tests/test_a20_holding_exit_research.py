from pathlib import Path
import pytest
from afip.exit_evidence_research import A20HoldingExitObservation, A20HoldingExitResearch
from afip.historical_replay_research import AppendOnlyResearchDataset

def observation(policy='R_STEP', bucket='HOLD_1_4_BARS', units=1, action='FULL_EXIT', realized=1.0):
 return A20HoldingExitObservation('CASE',policy,bucket,action,'M15','TREND','LONDON','NONE','NORMAL',units,4,3600,realized,2,.5,1,1,.1)

def test_records_and_ranks_same_context_after_cost(tmp_path: Path):
 d=AppendOnlyResearchDataset(tmp_path); r=A20HoldingExitResearch(d,2)
 assert r.record((observation(realized=1),observation(realized=2)))==2
 ranked=r.rank_recorded()
 assert len(ranked)==1 and ranked[0].sample_size==2 and ranked[0].expectancy_after_cost_r==1.4
 assert d.verify('a20_holding_exit_observations') and d.verify('a20_holding_exit_rankings')

def test_partial_and_runner_require_multiple_units():
 with pytest.raises(ValueError,match='multiple units'): observation(action='RUNNER')
 assert observation(units=2,action='PARTIAL_EXIT').position_units==2

def test_future_data_in_decision_fails_closed():
 with pytest.raises(ValueError,match='future data'):
  A20HoldingExitObservation('C','P','B','HOLD','M15','TREND','LONDON','NONE','NORMAL',1,1,60,0,1,0,1,1,0,future_data_used=True)
