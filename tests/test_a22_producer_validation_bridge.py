from pathlib import Path
from afip.exit_evidence_research import A21HoldingBucket,A21HoldingExitEvidenceProducer
from afip.exit_outcome_research import A16PolicySet,A16ResearchContext,PositionResearchCase
from afip.historical_replay_research import AppendOnlyResearchDataset
from afip.research_replay import ReplayCandle
def test_a21_producer_feeds_timestamped_a22_validation_source(tmp_path: Path):
 d=AppendOnlyResearchDataset(tmp_path);p=A21HoldingExitEvidenceProducer(d,buckets=(A21HoldingBucket('ALL',None),))
 c=A16ResearchContext('P','F','PLAN','2026-01-01T00:00:00Z','TREND','LONDON','OPEN','NONE','NORMAL','VERIFIED')
 case=PositionResearchCase('CASE','R','RUN','D','S','BUY',0,100)
 bars=(ReplayCandle('2026-01-01T00:00:00Z',100,101,99,100,1),ReplayCandle('2026-01-01T01:00:00Z',100,104,99,103,1))
 result=p.produce(case=case,policy_set=A16PolicySet(2),candles=bars,context=c,timeframe='H1',execution_cost_r=.1)
 records=d.records('a22_holding_exit_validation_observations')
 assert len(records)==len(result.observations)==7 and records[0]['record']['decision_timestamp_utc']=='2026-01-01T00:00:00Z'
 assert d.verify('a22_holding_exit_validation_observations')
