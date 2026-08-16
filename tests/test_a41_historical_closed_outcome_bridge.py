from pathlib import Path
from afip.historical_replay_research import AppendOnlyResearchDataset, HistoricalReplayRunner
from tools.afip_a41_historical_closed_outcome_bridge import build_report

def bars():
    return [dict(timestamp_utc=f"2026-01-01T0{i}:00:00Z",open=100+i,high=102+i,low=99+i,close=101+i,volume=10) for i in range(4)]

def test_a41_produces_via_existing_a21_and_is_idempotent(tmp_path: Path):
    source=AppendOnlyResearchDataset(tmp_path/"runtime/research/automatic/schema_v2")
    HistoricalReplayRunner(dataset=source,candidate_provider=lambda s: ({"direction":"BUY","pattern_family":"TEST","setup_id":"S","confidence":80},)).run(replay_id="R",research_run_id="RUN",dataset_version="D",scenario_id="GOLD-H1-DATA",candles=bars())
    first=build_report(tmp_path,maximum_cases=2); assert first["produced_cases"]==1 and first["produced_closed_outcomes"]==7
    assert first["execution_authority"]=="NONE"
    rows=AppendOnlyResearchDataset(tmp_path/"runtime/research").records("a22_holding_exit_validation_observations")
    assert rows[0]["record"]["direction"]=="BUY" and rows[0]["record"]["initial_risk_distance"]>=5
    assert rows[0]["record"]["selection_policy_version"]=="A41_V2_DEDUP_CONF60_COOLDOWN24"
    assert rows[0]["record"]["policy_variant_is_independent_trade"] is False
    second=build_report(tmp_path); assert second["produced_cases"]==0

def test_a41_waits_without_directional_candidates(tmp_path: Path):
    source=AppendOnlyResearchDataset(tmp_path/"runtime/research/automatic/schema_v2")
    HistoricalReplayRunner(dataset=source,candidate_provider=lambda s: ({"direction":"WAIT"},)).run(replay_id="R",research_run_id="RUN",dataset_version="D",scenario_id="GOLD-H1-DATA",candles=bars())
    report=build_report(tmp_path); assert report["status"]=="COMPLETE_NO_NEW_ELIGIBLE_CASES" and report["produced_cases"]==0

def test_a41_deduplicates_replay_generations_before_selection(tmp_path: Path):
    source=AppendOnlyResearchDataset(tmp_path/"runtime/research/automatic/schema_v2")
    provider=lambda s: ({"direction":"BUY","pattern_family":"TEST","setup_id":"S","confidence":80},)
    for replay_id in ("GEN1","GEN2"):
        HistoricalReplayRunner(dataset=source,candidate_provider=provider).run(replay_id=replay_id,research_run_id="RUN",dataset_version="D",scenario_id="GOLD-H1-DATA",candles=bars())
    report=build_report(tmp_path)
    assert report["raw_directional_candidates"]==8 and report["unique_candidates"]==4
    assert report["duplicate_replay_generation_candidates"]==4 and report["eligible_unique_candidates"]==1

def test_a41_excludes_unlabelled_final_candidate_before_eligibility(tmp_path: Path):
    source=AppendOnlyResearchDataset(tmp_path/"runtime/research/automatic/schema_v2")
    def provider(snapshot):
        confidence=80 if snapshot.replay_clock["replay_index"]==3 else 10
        return ({"direction":"BUY","pattern_family":"TEST","setup_id":"S","confidence":confidence},)
    HistoricalReplayRunner(dataset=source,candidate_provider=provider).run(replay_id="R",research_run_id="RUN",dataset_version="D",scenario_id="GOLD-H1-DATA",candles=bars())
    report=build_report(tmp_path)
    assert report["eligible_unique_candidates"]==0 and report["remaining_selected_cases"]==0
    assert report["rejection_reasons"]["NO_SUBSEQUENT_CLOSED_BAR_BEFORE_ELIGIBILITY"]==1
