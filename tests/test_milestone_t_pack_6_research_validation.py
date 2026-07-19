from pathlib import Path

import pytest

from afip.historical_replay_research import AppendOnlyResearchDataset
from afip.research_validation import (
    ResearchValidationEngine,
    ResearchValidationPolicy,
    RobustnessScenario,
    ValidationObservation,
    WalkForwardWindow,
)


def dataset(tmp_path):
    return AppendOnlyResearchDataset(tmp_path / "research" / "experimental" / "pack-6")


def observation(number, *, realized=1.0, policy="POLICY-A", segment="SEGMENT-A"):
    return ValidationObservation(
        observation_id=f"OBS-{number}",
        policy_id=policy,
        segment_id=segment,
        chronological_index=number,
        realized_r=realized,
        exit_quality_score=82 if realized >= 0 else 45,
        capital_preservation_score=85 if realized >= 0 else 50,
    )


def window(sequence=1, offset=0):
    return WalkForwardWindow(
        window_id=f"WF-{sequence}",
        sequence=sequence,
        train_start_index=1 + offset,
        train_end_index=3 + offset,
        validation_start_index=4 + offset,
        validation_end_index=5 + offset,
        forward_start_index=6 + offset,
        forward_end_index=7 + offset,
    )


def stable_observations(offset=0, policy="POLICY-A", segment="SEGMENT-A"):
    return [
        observation(index + offset, realized=value, policy=policy, segment=segment)
        for index, value in zip(range(1, 8), (1.2, 1.0, 1.1, 1.0, 0.9, 0.95, 1.05))
    ]


def test_walk_forward_window_requires_chronological_non_overlapping_ranges():
    with pytest.raises(ValueError, match="chronological"):
        WalkForwardWindow("BAD", 1, 1, 3, 3, 5, 6, 7)


def test_walk_forward_window_exposes_phase_sizes():
    value = window()
    assert (value.train_size, value.validation_size, value.forward_size) == (3, 2, 2)


def test_validation_observation_rejects_production_usable_state():
    with pytest.raises(ValueError, match="quarantined"):
        ValidationObservation("OBS", "P", "S", 1, 1.0, 80, 80, production_usable=True)


def test_validation_observation_can_be_created_from_mapping():
    value = ValidationObservation.from_mapping({
        "observation_id": "OBS-1", "policy_id": "P", "segment_id": "S",
        "chronological_index": 1, "realized_r": 1.5,
        "exit_quality_score": 80, "capital_preservation_score": 90,
    })
    assert value.realized_r == 1.5


def test_walk_forward_run_calculates_phase_metrics(tmp_path):
    engine = ResearchValidationEngine(dataset(tmp_path))
    result = engine.run_walk_forward(
        run_id="RUN-1", window=window(), observations=stable_observations(),
        policy_id="POLICY-A", segment_id="SEGMENT-A",
    )
    assert result.train_sample_size == 3
    assert result.validation_sample_size == 2
    assert result.forward_sample_size == 2
    assert result.forward_average_realized_r == pytest.approx(1.0)
    assert result.no_future_leakage is True


def test_walk_forward_stable_result_is_research_only(tmp_path):
    result = ResearchValidationEngine(dataset(tmp_path)).run_walk_forward(
        run_id="RUN-1", window=window(), observations=stable_observations(),
        policy_id="POLICY-A", segment_id="SEGMENT-A",
    )
    assert result.validation_status == "WALK_FORWARD_STABLE"
    assert result.production_usable is False
    assert result.research_state == "EXPERIMENTAL"


def test_walk_forward_rejects_missing_phase_data(tmp_path):
    with pytest.raises(ValueError, match="require observations"):
        ResearchValidationEngine(dataset(tmp_path)).run_walk_forward(
            run_id="RUN-1", window=window(), observations=stable_observations()[:5],
            policy_id="POLICY-A", segment_id="SEGMENT-A",
        )


def test_walk_forward_rejects_duplicate_observation_ids(tmp_path):
    values = stable_observations()
    values[-1] = values[-2]
    with pytest.raises(ValueError, match="unique"):
        ResearchValidationEngine(dataset(tmp_path)).run_walk_forward(
            run_id="RUN", window=window(), observations=values,
            policy_id="POLICY-A", segment_id="SEGMENT-A",
        )


def test_walk_forward_filters_policy_and_segment(tmp_path):
    other = [
        ValidationObservation(
            observation_id=f"OBS-B-{item.chronological_index}",
            policy_id="POLICY-B", segment_id="SEGMENT-B",
            chronological_index=item.chronological_index,
            realized_r=item.realized_r,
            exit_quality_score=item.exit_quality_score,
            capital_preservation_score=item.capital_preservation_score,
        )
        for item in stable_observations()
    ]
    values = stable_observations() + other
    result = ResearchValidationEngine(dataset(tmp_path)).run_walk_forward(
        run_id="RUN", window=window(), observations=values,
        policy_id="POLICY-A", segment_id="SEGMENT-A",
    )
    assert result.train_sample_size == 3


def test_robustness_scenario_penalty_is_deterministic():
    scenario = RobustnessScenario(
        "STRESS", spread_multiplier=2.0, slippage_r=0.1,
        volatility_multiplier=1.5, liquidity_penalty_r=0.1,
    )
    assert scenario.total_penalty_r == pytest.approx(0.34)


def test_robustness_scenario_rejects_negative_penalty():
    with pytest.raises(ValueError, match="cannot be negative"):
        RobustnessScenario("BAD", slippage_r=-0.1)


def test_robustness_evaluation_applies_stress(tmp_path):
    engine = ResearchValidationEngine(dataset(tmp_path))
    result = engine.run_robustness(
        run_id="ROB-1", observations=stable_observations(),
        policy_id="POLICY-A", segment_id="SEGMENT-A",
        scenarios=[RobustnessScenario("BASE"), RobustnessScenario("SPREAD", spread_multiplier=2.0)],
    )
    assert len(result) == 2
    assert result[1].stressed_average_realized_r < result[1].baseline_average_realized_r


def test_robustness_rejects_duplicate_scenarios(tmp_path):
    with pytest.raises(ValueError, match="unique"):
        ResearchValidationEngine(dataset(tmp_path)).run_robustness(
            run_id="ROB", observations=stable_observations(),
            policy_id="POLICY-A", segment_id="SEGMENT-A",
            scenarios=[RobustnessScenario("S"), RobustnessScenario("S")],
        )


def test_promotion_gate_blocks_insufficient_evidence(tmp_path):
    engine = ResearchValidationEngine(dataset(tmp_path))
    walk = engine.run_walk_forward(
        run_id="RUN", window=window(), observations=stable_observations(),
        policy_id="POLICY-A", segment_id="SEGMENT-A",
    )
    robust = engine.run_robustness(
        run_id="ROB", observations=stable_observations(),
        policy_id="POLICY-A", segment_id="SEGMENT-A",
        scenarios=[RobustnessScenario("BASE")],
    )
    gate = engine.evaluate_promotion_evidence(
        policy_id="POLICY-A", segment_id="SEGMENT-A",
        walk_forward_results=[walk], robustness_results=robust,
    )
    assert gate.promotion_evidence_eligible is False
    assert "minimum_walk_forward_runs_not_met" in gate.eligibility_reasons


def test_promotion_gate_can_mark_research_candidate_but_never_production(tmp_path):
    policy = ResearchValidationPolicy(
        minimum_walk_forward_runs=1,
        minimum_robustness_scenarios=2,
        minimum_forward_sample_size=2,
        minimum_temporal_stability_score=50,
        minimum_resilience_score=50,
        minimum_positive_forward_ratio=1.0,
        minimum_promotion_evidence_score=60,
    )
    engine = ResearchValidationEngine(dataset(tmp_path), policy=policy)
    walk = engine.run_walk_forward(
        run_id="RUN", window=window(), observations=stable_observations(),
        policy_id="POLICY-A", segment_id="SEGMENT-A",
    )
    robust = engine.run_robustness(
        run_id="ROB", observations=stable_observations(),
        policy_id="POLICY-A", segment_id="SEGMENT-A",
        scenarios=[RobustnessScenario("BASE"), RobustnessScenario("MILD", spread_multiplier=1.2)],
    )
    gate = engine.evaluate_promotion_evidence(
        policy_id="POLICY-A", segment_id="SEGMENT-A",
        walk_forward_results=[walk], robustness_results=robust,
    )
    assert gate.promotion_evidence_eligible is True
    assert gate.evidence_stage == "PROMOTION_CANDIDATE_RESEARCH_ONLY"
    assert gate.human_approval_required is True
    assert gate.automatic_promotion_allowed is False
    assert gate.production_usable is False


def test_validation_policy_rejects_invalid_thresholds():
    with pytest.raises(ValueError, match="positive"):
        ResearchValidationPolicy(minimum_walk_forward_runs=0)


def test_pack_6_datasets_are_append_only_and_verified(tmp_path):
    store = dataset(tmp_path)
    engine = ResearchValidationEngine(store)
    walk = engine.run_walk_forward(
        run_id="RUN", window=window(), observations=stable_observations(),
        policy_id="POLICY-A", segment_id="SEGMENT-A",
    )
    robust = engine.run_robustness(
        run_id="ROB", observations=stable_observations(),
        policy_id="POLICY-A", segment_id="SEGMENT-A",
        scenarios=[RobustnessScenario("BASE")],
    )
    engine.evaluate_promotion_evidence(
        policy_id="POLICY-A", segment_id="SEGMENT-A",
        walk_forward_results=[walk], robustness_results=robust,
    )
    for name in (
        "walk_forward_windows", "walk_forward_observations", "walk_forward_results",
        "robustness_scenarios", "robustness_results", "promotion_evidence_records",
    ):
        assert store.count(name) >= 1
        assert store.verify(name)


def test_dashboard_metadata_reports_quarantine_and_counts(tmp_path):
    store = dataset(tmp_path)
    engine = ResearchValidationEngine(store)
    engine.run_walk_forward(
        run_id="RUN", window=window(), observations=stable_observations(),
        policy_id="POLICY-A", segment_id="SEGMENT-A",
    )
    metadata = engine.dashboard_metadata()
    assert metadata["production_usable"] is False
    assert metadata["automatic_promotion_allowed"] is False
    assert metadata["dataset_counts"]["walk_forward_results"] == 1


def test_all_generated_records_remain_experimental(tmp_path):
    store = dataset(tmp_path)
    engine = ResearchValidationEngine(store)
    walk = engine.run_walk_forward(
        run_id="RUN", window=window(), observations=stable_observations(),
        policy_id="POLICY-A", segment_id="SEGMENT-A",
    )
    robust = engine.run_robustness(
        run_id="ROB", observations=stable_observations(),
        policy_id="POLICY-A", segment_id="SEGMENT-A",
        scenarios=[RobustnessScenario("BASE")],
    )
    engine.evaluate_promotion_evidence(
        policy_id="POLICY-A", segment_id="SEGMENT-A",
        walk_forward_results=[walk], robustness_results=robust,
    )
    for name in (
        "walk_forward_windows", "walk_forward_observations", "walk_forward_results",
        "robustness_scenarios", "robustness_results", "promotion_evidence_records",
    ):
        for envelope in store.records(name):
            assert envelope["record"]["research_state"] == "EXPERIMENTAL"
            assert envelope["record"]["production_usable"] is False


def test_module_contains_no_mt5_or_production_execution_calls():
    source = Path("afip/research_validation/runtime.py").read_text(encoding="utf-8")
    forbidden = ("order_send(", "order_check(", "positions_get(", "MetaTrader5", "production_runtime")
    assert not any(value in source for value in forbidden)
