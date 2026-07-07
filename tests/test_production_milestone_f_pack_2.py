from afip.runtime.production_milestone_f_self_evaluation_runtime import (
    run_production_milestone_f_self_evaluation,
)
from afip.self_evaluation import SelfEvaluationObservation, SelfEvaluationRuntime


def test_self_evaluation_blocks_records_without_market_regime():
    report = SelfEvaluationRuntime().run(
        [
            {
                "decision_status": "OPEN_POSITION",
                "expected_confidence": 0.91,
                "realized_result": 12.5,
                "data_quality": 0.95,
            }
        ]
    )

    data = report.as_dict()

    assert data["status"] == "SELF_EVALUATION_BLOCKED"
    assert data["decision"]["invalid_market_regime_count"] == 1
    assert data["architecture"]["market_regime_before_outcome_review"] is True


def test_self_evaluation_waits_for_closed_decision_observations():
    data = run_production_milestone_f_self_evaluation([])

    assert data["status"] == "SELF_EVALUATION_WAIT"
    assert data["ready"] is False
    assert data["decision"]["reason"] == "closed_decision_observations_required"


def test_self_evaluation_groups_by_regime_before_decision_status():
    data = run_production_milestone_f_self_evaluation(
        [
            {
                "market_regime": "trend",
                "decision_status": "open_position",
                "expected_confidence": 92,
                "realized_result": 18.0,
                "data_quality": 96,
                "knowledge_quality": 94,
            },
            {
                "market_regime": "trend",
                "decision_status": "open_position",
                "expected_confidence": 88,
                "realized_result": 10.0,
                "data_quality": 91,
                "knowledge_quality": 90,
            },
            {
                "market_regime": "range",
                "decision_status": "wait",
                "expected_confidence": 0.20,
                "realized_result": 0.0,
                "data_quality": 0.90,
                "knowledge_quality": 0.90,
            },
        ]
    )

    assert data["status"] == "SELF_EVALUATION_READY"
    assert data["profile_count"] == 2
    assert data["profiles"][0]["market_regime"] == "RANGE"
    assert data["profiles"][1]["market_regime"] == "TREND"
    assert data["architecture"]["production_learning_write"] is False


def test_self_evaluation_requires_review_when_confidence_is_misaligned():
    data = run_production_milestone_f_self_evaluation(
        [
            {
                "market_regime": "trend",
                "decision_status": "open_position",
                "expected_confidence": 0.98,
                "realized_result": -6.0,
                "data_quality": 0.90,
                "knowledge_quality": 0.90,
            }
        ]
    )

    assert data["status"] == "SELF_EVALUATION_REVIEW_REQUIRED"
    assert data["decision"]["review_profile_count"] == 1
    assert data["profiles"][0]["improvement_priority"] == "CONFIDENCE_ALIGNMENT_REVIEW"


def test_self_evaluation_observation_normalizes_percent_values():
    observation = SelfEvaluationObservation.from_mapping(
        {
            "market_regime": "expansion",
            "decision_status": "open_position",
            "expected_confidence": 75,
            "realized_result": 4.0,
            "data_quality": 80,
            "knowledge_quality": 70,
            "sample_weight": 2,
        }
    )

    assert observation.market_regime == "EXPANSION"
    assert observation.expected_confidence == 0.75
    assert observation.data_quality == 0.80
    assert observation.knowledge_quality == 0.70
    assert observation.weighted_result == 8.0
