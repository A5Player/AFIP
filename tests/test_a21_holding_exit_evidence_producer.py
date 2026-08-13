from pathlib import Path
import pytest
from afip.exit_evidence_research import A21HoldingBucket, A21HoldingExitEvidenceProducer
from afip.exit_outcome_research import A16PolicySet, A16ResearchContext, PositionResearchCase
from afip.historical_replay_research import AppendOnlyResearchDataset
from afip.research_replay import ReplayCandle

def context(): return A16ResearchContext('P','F','PLAN','2026-01-01T00:00:00Z','TREND','LONDON','OPEN','NONE','NORMAL','VERIFIED')
def case(units=1): return PositionResearchCase('CASE','REPLAY','RUN','DATA','SCENARIO','BUY',0,100,units)
def bars(): return (ReplayCandle('2026-01-01T00:00:00Z',100,150,50,100,1),ReplayCandle('2026-01-01T01:00:00Z',100,104,99,103,1),ReplayCandle('2026-01-01T02:00:00Z',103,105,102,104,1))
def producer(root,minimum=30): return A21HoldingExitEvidenceProducer(AppendOnlyResearchDataset(root),buckets=(A21HoldingBucket('SHORT',1),A21HoldingBucket('LONG',None)),minimum_sample_size=minimum)

def test_produces_from_subsequent_bars_and_records_costs(tmp_path: Path):
 result=producer(tmp_path).produce(case=case(),policy_set=A16PolicySet(2),candles=bars(),context=context(),timeframe='H1',execution_cost_r=.1,swap_cost_per_second_r=.00001)
 assert len(result.observations)==7 and all(item.holding_seconds>=3600 for item in result.observations)
 assert all(item.execution_authority=='NONE' for item in result.observations)
 assert AppendOnlyResearchDataset(tmp_path).verify('a20_holding_exit_observations')

def test_multiple_units_include_runner_and_duplicate_case_fails_closed(tmp_path: Path):
 value=producer(tmp_path); result=value.produce(case=case(2),policy_set=A16PolicySet(2),candles=bars(),context=context(),timeframe='H1',execution_cost_r=0)
 assert 'PARTIAL_RUNNER' in {item.policy_id for item in result.observations}
 with pytest.raises(ValueError,match='already exists'): value.produce(case=case(2),policy_set=A16PolicySet(2),candles=bars(),context=context(),timeframe='H1',execution_cost_r=0)

def test_requires_post_entry_closed_bar_and_configured_final_bucket(tmp_path: Path):
 with pytest.raises(ValueError,match='unbounded'): A21HoldingExitEvidenceProducer(AppendOnlyResearchDataset(tmp_path),buckets=(A21HoldingBucket('ONLY',1),))
 with pytest.raises(ValueError,match='subsequent closed bar'): producer(tmp_path).produce(case=case(),policy_set=A16PolicySet(2),candles=bars()[:1],context=context(),timeframe='H1',execution_cost_r=0)
