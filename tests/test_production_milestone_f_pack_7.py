from afip.ai_integration import AIIntegrationObservation, AIIntegrationRuntime
from afip.runtime.production_milestone_f_ai_integration_runtime import (
    run_production_milestone_f_ai_integration,
)


def test_ai_integration_blocks_records_without_market_regime():
    data = AIIntegrationRuntime().run(
        [
            {
                "signal_context": "breakout",
                "planned_runtime_weight": 0.62,
                "adaptation_quality": 0.90,
                "runtime_stability": 0.90,
                "model_confidence": 0.82,
                "data_quality": 0.90,
                "knowledge_quality": 0.90,
                "explainability_score": 0.90,
            }
        ]
    ).as_dict()

    assert data["status"] == "AI_INTEGRATION_BLOCKED"
    assert data["decision"]["invalid_market_regime_count"] == 1
    assert data["architecture"]["market_regime_before_signal_context"] is True


def test_ai_integration_waits_for_runtime_adaptation():
    data = run_production_milestone_f_ai_integration([])

    assert data["status"] == "AI_INTEGRATION_WAIT"
    assert data["ready"] is False
    assert data["decision"]["reason"] == "runtime_adaptation_required"


def test_ai_integration_orders_by_regime_before_signal_context():
    data = run_production_milestone_f_ai_integration(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "planned_runtime_weight": 0.75,
                "adaptation_quality": 0.90,
                "runtime_stability": 0.88,
                "model_confidence": 0.88,
                "data_quality": 0.90,
                "knowledge_quality": 0.90,
                "explainability_score": 0.86,
            },
            {
                "market_regime": "range",
                "signal_context": "mean_reversion",
                "planned_runtime_weight": 0.52,
                "adaptation_quality": 0.80,
                "runtime_stability": 0.78,
                "model_confidence": 0.70,
                "data_quality": 0.82,
                "knowledge_quality": 0.80,
                "explainability_score": 0.84,
            },
        ]
    )

    assert data["status"] == "AI_INTEGRATION_READY"
    assert data["profile_count"] == 2
    assert data["profiles"][0]["market_regime"] == "RANGE"
    assert data["profiles"][0]["signal_context"] == "MEAN_REVERSION"
    assert data["profiles"][1]["market_regime"] == "TREND"
    assert data["architecture"]["autonomous_execution"] is False
    assert data["architecture"]["ai_output_write"] is False


def test_ai_integration_calculates_plan_deterministically():
    data = run_production_milestone_f_ai_integration(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "planned_runtime_weight": 0.75,
                "adaptation_quality": 0.90,
                "runtime_stability": 0.88,
                "model_confidence": 0.88,
                "data_quality": 0.90,
                "knowledge_quality": 0.90,
                "explainability_score": 0.86,
                "integration_risk": 0.10,
            }
        ]
    )

    profile = data["profiles"][0]

    assert data["status"] == "AI_INTEGRATION_READY"
    assert profile["integration_quality"] == 0.89
    assert profile["ai_alignment_score"] == 0.835425
    assert profile["recommended_ai_weight"] == 0.626569
    assert profile["integration_state"] == "AI_ASSIST_READY"


def test_ai_integration_requires_review_for_low_explainability():
    data = run_production_milestone_f_ai_integration(
        [
            {
                "market_regime": "expansion",
                "signal_context": "momentum",
                "planned_runtime_weight": 0.70,
                "adaptation_quality": 0.84,
                "runtime_stability": 0.82,
                "model_confidence": 0.80,
                "data_quality": 0.84,
                "knowledge_quality": 0.82,
                "explainability_score": 0.40,
            }
        ]
    )

    assert data["status"] == "AI_INTEGRATION_REVIEW_REQUIRED"
    assert data["decision"]["review_profile_count"] == 1
    assert data["profiles"][0]["integration_state"] == "AI_REVIEW_REQUIRED"


def test_ai_integration_observation_normalizes_percent_values():
    observation = AIIntegrationObservation.from_mapping(
        {
            "market_regime": "range",
            "signal_context": "wait",
            "planned_runtime_weight": 60,
            "adaptation_quality": 90,
            "runtime_stability": 85,
            "model_confidence": 82,
            "data_quality": 88,
            "knowledge_quality": 84,
            "explainability_score": 91,
            "integration_risk": 20,
        }
    )

    assert observation.market_regime == "RANGE"
    assert observation.planned_runtime_weight == 0.60
    assert observation.adaptation_quality == 0.90
    assert observation.runtime_stability == 0.85
    assert observation.model_confidence == 0.82
    assert observation.data_quality == 0.88
    assert observation.knowledge_quality == 0.84
    assert observation.explainability_score == 0.91
    assert observation.integration_risk == 0.20
