from afip.runtime.production_milestone_f_validation_runtime import (
    run_production_milestone_f_validation,
)
from afip.validation import ValidationObservation, ValidationRuntime


def test_validation_blocks_records_without_market_regime():
    data = ValidationRuntime().run(
        [
            {
                "signal_context": "continuation",
                "ai_alignment_score": 0.82,
                "recommended_ai_weight": 0.56,
                "integration_quality": 0.88,
                "data_quality": 0.90,
                "knowledge_quality": 0.88,
                "explainability_score": 0.86,
                "runtime_stability": 0.88,
                "validation_sample_quality": 0.90,
                "validation_consistency": 0.87,
            }
        ]
    ).as_dict()

    assert data["status"] == "VALIDATION_BLOCKED"
    assert data["decision"]["invalid_market_regime_count"] == 1
    assert data["architecture"]["market_regime_before_signal_context"] is True


def test_validation_waits_for_ai_integration():
    data = run_production_milestone_f_validation([])

    assert data["status"] == "VALIDATION_WAIT"
    assert data["ready"] is False
    assert data["decision"]["reason"] == "ai_integration_required"


def test_validation_orders_by_regime_before_signal_context():
    data = run_production_milestone_f_validation(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "ai_alignment_score": 0.82,
                "recommended_ai_weight": 0.56,
                "integration_quality": 0.88,
                "data_quality": 0.90,
                "knowledge_quality": 0.88,
                "explainability_score": 0.86,
                "runtime_stability": 0.88,
                "validation_sample_quality": 0.90,
                "validation_consistency": 0.87,
            },
            {
                "market_regime": "range",
                "signal_context": "mean_reversion",
                "ai_alignment_score": 0.76,
                "recommended_ai_weight": 0.48,
                "integration_quality": 0.82,
                "data_quality": 0.84,
                "knowledge_quality": 0.83,
                "explainability_score": 0.81,
                "runtime_stability": 0.80,
                "validation_sample_quality": 0.82,
                "validation_consistency": 0.80,
            },
        ]
    )

    assert data["status"] == "VALIDATION_READY"
    assert data["profile_count"] == 2
    assert data["profiles"][0]["market_regime"] == "RANGE"
    assert data["profiles"][0]["signal_context"] == "MEAN_REVERSION"
    assert data["profiles"][1]["market_regime"] == "TREND"
    assert data["architecture"]["production_write_allowed"] is False
    assert data["architecture"]["validation_before_production_readiness"] is True


def test_validation_calculates_score_deterministically():
    data = run_production_milestone_f_validation(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "ai_alignment_score": 0.835425,
                "recommended_ai_weight": 0.626569,
                "integration_quality": 0.89,
                "data_quality": 0.90,
                "knowledge_quality": 0.90,
                "explainability_score": 0.86,
                "runtime_stability": 0.88,
                "validation_sample_quality": 0.92,
                "validation_consistency": 0.87,
                "validation_risk": 0.12,
            }
        ]
    )

    profile = data["profiles"][0]

    assert data["status"] == "VALIDATION_READY"
    assert profile["evidence_quality"] == 0.892
    assert profile["validation_score"] == 0.799536
    assert profile["approved_runtime_weight"] == 0.500964
    assert profile["validation_state"] == "VALIDATION_READY"


def test_validation_requires_review_for_low_sample_quality():
    data = run_production_milestone_f_validation(
        [
            {
                "market_regime": "expansion",
                "signal_context": "momentum",
                "ai_alignment_score": 0.80,
                "recommended_ai_weight": 0.55,
                "integration_quality": 0.84,
                "data_quality": 0.84,
                "knowledge_quality": 0.82,
                "explainability_score": 0.80,
                "runtime_stability": 0.82,
                "validation_sample_quality": 0.40,
                "validation_consistency": 0.82,
            }
        ]
    )

    assert data["status"] == "VALIDATION_REVIEW_REQUIRED"
    assert data["decision"]["review_profile_count"] == 1
    assert data["profiles"][0]["validation_state"] == "VALIDATION_REVIEW_REQUIRED"


def test_validation_observation_normalizes_percent_values():
    observation = ValidationObservation.from_mapping(
        {
            "market_regime": "range",
            "signal_context": "wait",
            "ai_alignment_score": 82,
            "recommended_ai_weight": 60,
            "integration_quality": 90,
            "data_quality": 88,
            "knowledge_quality": 84,
            "explainability_score": 91,
            "runtime_stability": 85,
            "validation_sample_quality": 89,
            "validation_consistency": 83,
            "validation_risk": 20,
        }
    )

    assert observation.market_regime == "RANGE"
    assert observation.ai_alignment_score == 0.82
    assert observation.recommended_ai_weight == 0.60
    assert observation.integration_quality == 0.90
    assert observation.data_quality == 0.88
    assert observation.knowledge_quality == 0.84
    assert observation.explainability_score == 0.91
    assert observation.runtime_stability == 0.85
    assert observation.validation_sample_quality == 0.89
    assert observation.validation_consistency == 0.83
    assert observation.validation_risk == 0.20
