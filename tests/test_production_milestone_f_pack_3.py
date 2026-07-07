from afip.adaptive_confidence import AdaptiveConfidenceObservation, AdaptiveConfidenceRuntime
from afip.runtime.production_milestone_f_adaptive_confidence_runtime import (
    run_production_milestone_f_adaptive_confidence,
)


def test_adaptive_confidence_blocks_records_without_market_regime():
    data = AdaptiveConfidenceRuntime().run(
        [
            {
                "signal_context": "breakout",
                "raw_confidence": 0.92,
                "self_evaluation_score": 0.86,
                "data_quality": 0.91,
                "knowledge_quality": 0.89,
            }
        ]
    ).as_dict()

    assert data["status"] == "ADAPTIVE_CONFIDENCE_BLOCKED"
    assert data["decision"]["invalid_market_regime_count"] == 1
    assert data["architecture"]["market_regime_before_signal_context"] is True


def test_adaptive_confidence_waits_for_evidence():
    data = run_production_milestone_f_adaptive_confidence([])

    assert data["status"] == "ADAPTIVE_CONFIDENCE_WAIT"
    assert data["ready"] is False
    assert data["decision"]["reason"] == "confidence_evidence_required"


def test_adaptive_confidence_groups_by_regime_before_signal_context():
    data = run_production_milestone_f_adaptive_confidence(
        [
            {
                "market_regime": "trend",
                "signal_context": "breakout",
                "raw_confidence": 0.90,
                "self_evaluation_score": 0.88,
                "data_quality": 0.94,
                "knowledge_quality": 0.92,
                "stability_score": 0.87,
                "sample_size": 4,
            },
            {
                "market_regime": "range",
                "signal_context": "mean_reversion",
                "raw_confidence": 0.62,
                "self_evaluation_score": 0.75,
                "data_quality": 0.80,
                "knowledge_quality": 0.78,
                "stability_score": 0.73,
                "sample_size": 3,
            },
        ]
    )

    assert data["status"] == "ADAPTIVE_CONFIDENCE_READY"
    assert data["profile_count"] == 2
    assert data["profiles"][0]["market_regime"] == "RANGE"
    assert data["profiles"][0]["signal_context"] == "MEAN_REVERSION"
    assert data["profiles"][1]["market_regime"] == "TREND"
    assert data["architecture"]["confidence_runtime_write"] is False


def test_adaptive_confidence_reduces_confidence_when_evidence_is_weaker():
    data = run_production_milestone_f_adaptive_confidence(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "raw_confidence": 0.90,
                "self_evaluation_score": 0.70,
                "data_quality": 0.70,
                "knowledge_quality": 0.70,
                "stability_score": 0.70,
                "sample_size": 1,
            }
        ]
    )

    profile = data["profiles"][0]

    assert data["status"] == "ADAPTIVE_CONFIDENCE_READY"
    assert profile["adaptive_confidence"] == 0.82
    assert profile["confidence_adjustment"] == -0.08
    assert profile["confidence_state"] == "CONFIDENCE_MAINTAINED"


def test_adaptive_confidence_requires_review_for_low_data_quality():
    data = run_production_milestone_f_adaptive_confidence(
        [
            {
                "market_regime": "expansion",
                "signal_context": "momentum",
                "raw_confidence": 0.72,
                "self_evaluation_score": 0.82,
                "data_quality": 0.40,
                "knowledge_quality": 0.84,
                "stability_score": 0.81,
            }
        ]
    )

    assert data["status"] == "ADAPTIVE_CONFIDENCE_REVIEW_REQUIRED"
    assert data["decision"]["review_profile_count"] == 1
    assert data["profiles"][0]["confidence_state"] == "DATA_REVIEW_REQUIRED"


def test_adaptive_confidence_observation_normalizes_percent_values():
    observation = AdaptiveConfidenceObservation.from_mapping(
        {
            "market_regime": "range",
            "signal_context": "wait",
            "raw_confidence": 75,
            "self_evaluation_score": 80,
            "data_quality": 90,
            "knowledge_quality": 85,
            "stability_score": 70,
            "sample_size": 2,
        }
    )

    assert observation.market_regime == "RANGE"
    assert observation.raw_confidence == 0.75
    assert observation.self_evaluation_score == 0.80
    assert observation.data_quality == 0.90
    assert observation.knowledge_quality == 0.85
    assert observation.stability_score == 0.70
    assert observation.weighted_raw_confidence == 1.5
