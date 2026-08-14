from pathlib import Path
import pytest
from afip.exit_evidence_research import (A24DecisionContext,A24OutcomeEvidence,
    A24TPVolumePolicy,A24TPVolumeResearch)
from afip.historical_replay_research import AppendOnlyResearchDataset

def context(**overrides):
    values=dict(research_case_id='CASE-1',decision_timestamp_utc='2026-01-01T01:00:00Z',
        direction='BUY',current_price=109.85,target_price=110,point_size=.01,
        initial_risk_points=100,atr_points=80,spread_points=10,tick_volume=140,
        volume_baseline=100,volume_sample_size=30,favorable_wick_ratio=.1,
        unrealized_r=.9,maximum_favorable_r=1,position_units=2,holding_bars=5,
        timeframe='H1',market_regime='TREND',session_name='LONDON',
        event_window='NONE',calendar_context='NORMAL')
    values.update(overrides);return A24DecisionContext(**values)

def test_strong_volume_inside_buffer_proposes_runner_without_authority(tmp_path:Path):
    item=A24TPVolumeResearch(AppendOnlyResearchDataset(tmp_path)).advise(context())
    assert item.recommended_action=='RUNNER' and item.within_approach_buffer
    assert item.no_order_sent and item.execution_authority=='NONE'

def test_weak_volume_proposes_partial_only_for_multiple_units(tmp_path:Path):
    research=A24TPVolumeResearch(AppendOnlyResearchDataset(tmp_path))
    assert research.advise(context(tick_volume=50)).recommended_action=='PARTIAL_EXIT'

def test_outside_buffer_holds_and_target_reached_is_explicit(tmp_path:Path):
    d=AppendOnlyResearchDataset(tmp_path);r=A24TPVolumeResearch(d)
    assert r.advise(context(research_case_id='FAR',current_price=108)).recommended_action=='HOLD'
    assert r.advise(context(research_case_id='HIT',current_price=110)).recommended_action=='FULL_EXIT'

def test_insufficient_tick_volume_evidence_fails_to_exit_watch(tmp_path:Path):
    item=A24TPVolumeResearch(AppendOnlyResearchDataset(tmp_path)).advise(
        context(volume_sample_size=3))
    assert item.recommended_action=='EXIT_WATCH' and item.volume_state=='INSUFFICIENT'

def test_decision_rejects_future_data_and_non_tick_volume():
    with pytest.raises(ValueError,match='leakage-free'):
        context(future_data_used=True)
    with pytest.raises(ValueError,match='tick-volume provenance'):
        context(volume_source='CENTRALIZED_REAL_VOLUME')

def test_outcome_is_separate_and_feeds_existing_a22_validation(tmp_path:Path):
    d=AppendOnlyResearchDataset(tmp_path);r=A24TPVolumeResearch(d)
    decision=r.advise(context())
    r.record_outcome(A24OutcomeEvidence(decision.decision_id,'2026-01-01T02:00:00Z',
        1.1,.1,0,1.3,.2,3600))
    source=d.records('a22_holding_exit_validation_observations')[0]['record']
    assert source['decision_timestamp_utc']=='2026-01-01T01:00:00Z'
    assert source['policy_id']=='A24:RUNNER' and source['net_realized_r']==1
    assert d.verify('a24_tp_volume_decisions') and d.verify('a24_tp_volume_outcomes')

def test_outcome_requires_recorded_decision_and_is_append_once(tmp_path:Path):
    d=AppendOnlyResearchDataset(tmp_path);r=A24TPVolumeResearch(d)
    missing=A24OutcomeEvidence('MISSING','2026-01-01T02:00:00Z',0,0,0,0,0,0)
    with pytest.raises(ValueError,match='recorded advisory'):
        r.record_outcome(missing)
    decision=r.advise(context());outcome=A24OutcomeEvidence(
        decision.decision_id,'2026-01-01T02:00:00Z',0,0,0,0,0,0)
    r.record_outcome(outcome)
    with pytest.raises(ValueError,match='already exists'):
        r.record_outcome(outcome)

def test_policy_validation_is_fail_closed():
    with pytest.raises(ValueError): A24TPVolumePolicy(weak_volume_ratio=2,strong_volume_ratio=1)
