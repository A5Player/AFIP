from afip.experience_knowledge import ExperienceKnowledgeObservation, ExperienceKnowledgeRuntime
from afip.runtime.production_milestone_f_experience_knowledge_runtime import (
    run_production_milestone_f_experience_knowledge,
)


def test_experience_knowledge_blocks_records_without_market_regime():
    data = ExperienceKnowledgeRuntime().run(
        [
            {
                "signal_context": "breakout",
                "realized_result": 0.40,
                "adaptive_confidence": 0.86,
                "self_evaluation_score": 0.84,
                "data_quality": 0.90,
                "knowledge_quality": 0.88,
            }
        ]
    ).as_dict()

    assert data["status"] == "EXPERIENCE_KNOWLEDGE_BLOCKED"
    assert data["decision"]["invalid_market_regime_count"] == 1
    assert data["architecture"]["market_regime_before_signal_context"] is True


def test_experience_knowledge_waits_for_closed_experience():
    data = run_production_milestone_f_experience_knowledge([])

    assert data["status"] == "EXPERIENCE_KNOWLEDGE_WAIT"
    assert data["ready"] is False
    assert data["decision"]["reason"] == "experience_observations_required"


def test_experience_knowledge_groups_by_regime_before_signal_context():
    data = run_production_milestone_f_experience_knowledge(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "realized_result": 0.80,
                "adaptive_confidence": 0.88,
                "self_evaluation_score": 0.86,
                "data_quality": 0.92,
                "knowledge_quality": 0.90,
                "recency_score": 0.84,
                "sample_weight": 3,
            },
            {
                "market_regime": "range",
                "signal_context": "mean_reversion",
                "realized_result": 0.35,
                "adaptive_confidence": 0.74,
                "self_evaluation_score": 0.78,
                "data_quality": 0.82,
                "knowledge_quality": 0.80,
                "recency_score": 0.77,
                "sample_weight": 2,
            },
        ]
    )

    assert data["status"] == "EXPERIENCE_KNOWLEDGE_READY"
    assert data["profile_count"] == 2
    assert data["profiles"][0]["market_regime"] == "RANGE"
    assert data["profiles"][0]["signal_context"] == "MEAN_REVERSION"
    assert data["profiles"][1]["market_regime"] == "TREND"
    assert data["architecture"]["experience_runtime_write"] is False


def test_experience_knowledge_calculates_expectancy_and_score_deterministically():
    data = run_production_milestone_f_experience_knowledge(
        [
            {
                "market_regime": "trend",
                "signal_context": "breakout",
                "realized_result": 1.0,
                "adaptive_confidence": 0.90,
                "self_evaluation_score": 0.80,
                "data_quality": 0.80,
                "knowledge_quality": 0.80,
                "recency_score": 0.70,
                "sample_weight": 1,
            },
            {
                "market_regime": "trend",
                "signal_context": "breakout",
                "realized_result": -0.5,
                "adaptive_confidence": 0.70,
                "self_evaluation_score": 0.70,
                "data_quality": 0.70,
                "knowledge_quality": 0.70,
                "recency_score": 0.70,
                "sample_weight": 1,
            },
        ]
    )

    profile = data["profiles"][0]

    assert data["status"] == "EXPERIENCE_KNOWLEDGE_READY"
    assert profile["expectancy"] == 0.25
    assert profile["positive_rate"] == 0.5
    assert profile["average_reliability_score"] == 0.75
    assert profile["experience_score"] == 0.6625
    assert profile["knowledge_state"] == "EXPERIENCE_OBSERVED"


def test_experience_knowledge_requires_review_for_low_knowledge_quality():
    data = run_production_milestone_f_experience_knowledge(
        [
            {
                "market_regime": "expansion",
                "signal_context": "momentum",
                "realized_result": 0.60,
                "adaptive_confidence": 0.82,
                "self_evaluation_score": 0.82,
                "data_quality": 0.82,
                "knowledge_quality": 0.42,
                "recency_score": 0.80,
            }
        ]
    )

    assert data["status"] == "EXPERIENCE_KNOWLEDGE_REVIEW_REQUIRED"
    assert data["decision"]["review_profile_count"] == 1
    assert data["profiles"][0]["knowledge_state"] == "KNOWLEDGE_REVIEW_REQUIRED"


def test_experience_knowledge_observation_normalizes_percent_values():
    observation = ExperienceKnowledgeObservation.from_mapping(
        {
            "market_regime": "range",
            "signal_context": "wait",
            "realized_result": 0.5,
            "adaptive_confidence": 75,
            "self_evaluation_score": 80,
            "data_quality": 90,
            "knowledge_quality": 85,
            "recency_score": 70,
            "sample_weight": 2,
        }
    )

    assert observation.market_regime == "RANGE"
    assert observation.adaptive_confidence == 0.75
    assert observation.self_evaluation_score == 0.80
    assert observation.data_quality == 0.90
    assert observation.knowledge_quality == 0.85
    assert observation.recency_score == 0.70
    assert observation.reliability_score == 0.80
    assert observation.weighted_reliability == 1.6
