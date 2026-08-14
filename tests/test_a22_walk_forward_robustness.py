from pathlib import Path
import pytest
from afip.exit_evidence_research import A22RobustnessPolicy, A22WalkForwardValidator, A22WalkForwardWindow
from afip.historical_replay_research import AppendOnlyResearchDataset

def windows(): return (
 A22WalkForwardWindow('TRAIN-1','TRAIN','2026-01-01T00:00:00Z','2026-02-01T00:00:00Z'),
 A22WalkForwardWindow('VALID-1','VALIDATION','2026-02-01T00:00:00Z','2026-03-01T00:00:00Z'),
 A22WalkForwardWindow('BLIND-1','BLIND_FORWARD','2026-03-01T00:00:00Z','2026-04-01T00:00:00Z'))
def record(timestamp,net): return {'policy_id':'R_STEP','holding_bucket_id':'SHORT','timeframe':'H1','market_regime':'TREND','session_name':'LONDON','event_window':'NONE','calendar_context':'NORMAL','decision_timestamp_utc':timestamp,'net_realized_r':net,'mfe_r':2,'mae_r':.5,'holding_seconds':3600}
def validator(root,minimum=2,drift=.5): return A22WalkForwardValidator(AppendOnlyResearchDataset(root),windows=windows(),policy=A22RobustnessPolicy(minimum,drift))
def append_phase(dataset,month,values):
 for index,value in enumerate(values,1): dataset.append('a22_holding_exit_validation_observations',record(f'2026-{month:02d}-{index:02d}T00:00:00Z',value))

def test_robust_partition_has_confidence_and_append_only_result(tmp_path: Path):
 d=AppendOnlyResearchDataset(tmp_path);append_phase(d,1,[1,1]);append_phase(d,2,[1,1]);append_phase(d,3,[1,1])
 item=validator(tmp_path).validate_recorded()[0]
 assert item.status=='ROBUST' and item.blind_forward_confidence_low_r==1 and item.automatic_promotion_allowed is False
 assert item.sensitivity_pass and item.blind_forward_net_profit_r==2
 assert d.verify('a22_holding_exit_validation_results')
 with pytest.raises(ValueError,match='already exists'): validator(tmp_path).validate_recorded()

def test_overfit_and_drift_are_rejected(tmp_path: Path):
 d=AppendOnlyResearchDataset(tmp_path);append_phase(d,1,[2,2]);append_phase(d,2,[-1,-1]);append_phase(d,3,[-1,-1])
 item=validator(tmp_path,drift=.25).validate_recorded()[0]
 assert item.status=='REJECTED' and item.overfitting_detected and item.drift_detected

def test_insufficient_partition_is_recorded_as_wait(tmp_path: Path):
 d=AppendOnlyResearchDataset(tmp_path);append_phase(d,1,[1]);append_phase(d,2,[1]);append_phase(d,3,[1])
 item=validator(tmp_path,minimum=2).validate_recorded()[0]
 assert item.status=='WAIT' and item.reason=='minimum_sample_not_met'

def test_windows_must_be_chronological_train_validation_blind(tmp_path: Path):
 with pytest.raises(ValueError,match='ordered'):
  A22WalkForwardValidator(AppendOnlyResearchDataset(tmp_path),windows=tuple(reversed(windows())),policy=A22RobustnessPolicy(2,.5))
