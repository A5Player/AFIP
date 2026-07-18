from pathlib import Path

import pytest

from afip.exit_evidence_research import (
    ContextSegment,
    EvidenceObservation,
    ExitEvidenceResearchEngine,
)
from afip.historical_replay_research import AppendOnlyResearchDataset


def dataset(tmp_path):
    return AppendOnlyResearchDataset(tmp_path / "research" / "experimental" / "exit-pack-5")


def segment(**overrides):
    values = {
        "market_regime": "TRENDING",
        "market_structure": "BULLISH",
        "liquidity_state": "NORMAL",
        "trend_state": "STRONG",
        "volatility_state": "MEDIUM",
        "trading_session": "LONDON",
        "direction": "BUY",
        "pattern_family": "PULLBACK",
    }
    values.update(overrides)
    return ContextSegment.from_mapping(values)


def observation(number, policy="POLICY-A", realized=1.0, context=None):
    return EvidenceObservation(
        observation_id=f"OBS-{number}",
        position_case_id=f"CASE-{number}",
        policy_id=policy,
        realized_r=realized,
        exit_quality_score=80 if realized >= 0 else 40,
        capital_preservation_score=85 if realized >= 0 else 45,
        profit_capture_ratio=0.75 if realized > 0 else 0.0,
        maximum_adverse_excursion_r=0.25 if realized >= 0 else 1.0,
        bars_held=4,
        segment=context or segment(),
    )


def test_context_segment_is_deterministic_and_normalized():
    value = segment(market_regime="trending market", trading_session="new york")
    assert value.market_regime == "TRENDING_MARKET"
    assert value.trading_session == "NEW_YORK"
    assert value.segment_id.endswith("BUY|PULLBACK")


def test_context_segment_rejects_non_trading_direction():
    with pytest.raises(ValueError, match="BUY or SELL"):
        segment(direction="WAIT")


def test_observation_from_outcome_and_context_mapping():
    outcome = {
        "position_case_id": "CASE-1", "policy_id": "P1", "realized_r": 1.5,
        "exit_quality_score": 88, "capital_preservation_score": 90,
        "profit_capture_ratio": 0.8, "maximum_adverse_excursion_r": 0.2, "bars_held": 5,
    }
    value = EvidenceObservation.from_mappings(observation_id="OBS-1", outcome=outcome, context=segment().as_dict())
    assert value.policy_id == "P1"
    assert value.realized_r == 1.5


def test_observation_requires_quarantined_state():
    with pytest.raises(ValueError, match="quarantined"):
        EvidenceObservation(
            observation_id="OBS", position_case_id="CASE", policy_id="P",
            realized_r=1, exit_quality_score=80, capital_preservation_score=80,
            profit_capture_ratio=0.8, maximum_adverse_excursion_r=0.2,
            bars_held=1, segment=segment(), production_usable=True,
        )


def test_aggregate_calculates_segment_metrics(tmp_path):
    engine = ExitEvidenceResearchEngine(dataset(tmp_path), minimum_sample_size=3)
    summary = engine.aggregate([observation(1, realized=1), observation(2, realized=2), observation(3, realized=-0.5)])[0]
    assert summary.sample_size == 3
    assert summary.profitable_count == 2
    assert summary.loss_count == 1
    assert summary.win_rate == pytest.approx(2 / 3)
    assert summary.average_realized_r == pytest.approx(2.5 / 3)


def test_aggregate_separates_market_contexts(tmp_path):
    engine = ExitEvidenceResearchEngine(dataset(tmp_path))
    summaries = engine.aggregate([
        observation(1),
        observation(2, context=segment(market_regime="RANGING")),
    ])
    assert len(summaries) == 2
    assert len({item.segment_id for item in summaries}) == 2


def test_aggregate_separates_policies(tmp_path):
    summaries = ExitEvidenceResearchEngine(dataset(tmp_path)).aggregate([
        observation(1, policy="A"), observation(2, policy="B")
    ])
    assert [item.policy_id for item in summaries] == ["A", "B"]


def test_insufficient_sample_remains_ineligible(tmp_path):
    store = dataset(tmp_path)
    ExitEvidenceResearchEngine(store, minimum_sample_size=10).aggregate([observation(1)])
    evaluation = store.records("exit_evidence_evaluations")[0]["record"]
    assert evaluation["evidence_eligible"] is False
    assert "minimum_sample_size_not_met" in evaluation["eligibility_reasons"]


def test_negative_expectancy_is_not_eligible(tmp_path):
    store = dataset(tmp_path)
    values = [observation(i, realized=-0.5) for i in range(1, 4)]
    ExitEvidenceResearchEngine(store, minimum_sample_size=3).aggregate(values)
    evaluation = store.records("exit_evidence_evaluations")[0]["record"]
    assert "positive_expectancy_not_demonstrated" in evaluation["eligibility_reasons"]


def test_evidence_can_be_research_eligible_without_production_promotion(tmp_path):
    store = dataset(tmp_path)
    values = [observation(i, realized=1.2) for i in range(1, 31)]
    ExitEvidenceResearchEngine(store, minimum_sample_size=30).aggregate(values)
    evaluation = store.records("exit_evidence_evaluations")[0]["record"]
    assert evaluation["evidence_eligible"] is True
    assert evaluation["automatic_promotion_allowed"] is False
    assert evaluation["production_usable"] is False


def test_policy_comparison_never_selects_winner(tmp_path):
    engine = ExitEvidenceResearchEngine(dataset(tmp_path), minimum_sample_size=1)
    summaries = engine.aggregate([observation(1, policy="A", realized=1), observation(2, policy="B", realized=0.5)])
    comparisons = engine.compare(summaries)
    assert len(comparisons) == 1
    assert comparisons[0].selected_policy_id is None
    assert comparisons[0].comparison_status == "RESEARCH_ONLY_NO_SELECTION"


def test_policy_comparison_only_compares_shared_segment(tmp_path):
    engine = ExitEvidenceResearchEngine(dataset(tmp_path))
    summaries = engine.aggregate([
        observation(1, policy="A"),
        observation(2, policy="B", context=segment(market_regime="RANGING")),
    ])
    assert engine.compare(summaries) == ()


def test_duplicate_observation_ids_are_rejected(tmp_path):
    engine = ExitEvidenceResearchEngine(dataset(tmp_path))
    with pytest.raises(ValueError, match="unique"):
        engine.aggregate([observation(1), observation(1)])


def test_empty_aggregation_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="at least one"):
        ExitEvidenceResearchEngine(dataset(tmp_path)).aggregate([])


def test_minimum_sample_size_must_be_positive(tmp_path):
    with pytest.raises(ValueError, match="positive"):
        ExitEvidenceResearchEngine(dataset(tmp_path), minimum_sample_size=0)


def test_new_datasets_are_append_only_and_verified(tmp_path):
    store = dataset(tmp_path)
    engine = ExitEvidenceResearchEngine(store)
    summaries = engine.aggregate([observation(1, policy="A"), observation(2, policy="B")])
    engine.compare(summaries)
    for name in (
        "exit_evidence_observations", "exit_context_segments", "exit_evidence_summaries",
        "exit_evidence_evaluations", "exit_policy_comparisons",
    ):
        assert store.count(name) >= 1
        assert store.verify(name)


def test_dashboard_metadata_includes_pack_5_datasets(tmp_path):
    store = dataset(tmp_path)
    ExitEvidenceResearchEngine(store).aggregate([observation(1)])
    metadata = store.dashboard_metadata()
    assert metadata["dataset_counts"]["exit_evidence_observations"] == 1
    assert metadata["dataset_counts"]["exit_evidence_summaries"] == 1
    assert metadata["production_usable"] is False


def test_all_generated_records_remain_experimental(tmp_path):
    store = dataset(tmp_path)
    engine = ExitEvidenceResearchEngine(store)
    summaries = engine.aggregate([observation(1, policy="A"), observation(2, policy="B")])
    engine.compare(summaries)
    for name in (
        "exit_evidence_observations", "exit_context_segments", "exit_evidence_summaries",
        "exit_evidence_evaluations", "exit_policy_comparisons",
    ):
        for envelope in store.records(name):
            assert envelope["record"]["research_state"] == "EXPERIMENTAL"
            assert envelope["record"]["production_usable"] is False


def test_module_contains_no_mt5_or_production_execution_calls():
    source = Path("afip/exit_evidence_research/runtime.py").read_text(encoding="utf-8")
    forbidden = ("order_send(", "order_check(", "positions_get(", "MetaTrader5", "production_runtime")
    assert not any(value in source for value in forbidden)
