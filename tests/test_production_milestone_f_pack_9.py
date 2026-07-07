from afip.production_readiness import ProductionReadinessObservation, ProductionReadinessRuntime
from afip.runtime.production_milestone_f_production_readiness_runtime import (
    run_production_milestone_f_production_readiness,
)


def test_production_readiness_blocks_records_without_market_regime():
    data = ProductionReadinessRuntime().run(
        [
            {
                "signal_context": "continuation",
                "validation_score": 0.80,
                "approved_runtime_weight": 0.50,
                "evidence_quality": 0.88,
                "data_quality": 0.90,
                "knowledge_quality": 0.88,
                "explainability_score": 0.86,
                "runtime_stability": 0.88,
                "validation_sample_quality": 0.90,
                "validation_consistency": 0.87,
                "deployment_control_quality": 0.88,
                "monitoring_quality": 0.86,
                "rollback_readiness": 0.84,
            }
        ]
    ).as_dict()

    assert data["status"] == "PRODUCTION_READINESS_BLOCKED"
    assert data["decision"]["invalid_market_regime_count"] == 1
    assert data["architecture"]["market_regime_before_signal_context"] is True


def test_production_readiness_waits_for_validation():
    data = run_production_milestone_f_production_readiness([])

    assert data["status"] == "PRODUCTION_READINESS_WAIT"
    assert data["ready"] is False
    assert data["decision"]["reason"] == "validation_required"


def test_production_readiness_orders_by_regime_before_signal_context():
    data = run_production_milestone_f_production_readiness(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "validation_score": 0.80,
                "approved_runtime_weight": 0.50,
                "evidence_quality": 0.88,
                "data_quality": 0.90,
                "knowledge_quality": 0.88,
                "explainability_score": 0.86,
                "runtime_stability": 0.88,
                "validation_sample_quality": 0.90,
                "validation_consistency": 0.87,
                "deployment_control_quality": 0.88,
                "monitoring_quality": 0.86,
                "rollback_readiness": 0.84,
            },
            {
                "market_regime": "range",
                "signal_context": "mean_reversion",
                "validation_score": 0.76,
                "approved_runtime_weight": 0.44,
                "evidence_quality": 0.82,
                "data_quality": 0.84,
                "knowledge_quality": 0.83,
                "explainability_score": 0.81,
                "runtime_stability": 0.80,
                "validation_sample_quality": 0.82,
                "validation_consistency": 0.80,
                "deployment_control_quality": 0.83,
                "monitoring_quality": 0.81,
                "rollback_readiness": 0.80,
            },
        ]
    )

    assert data["status"] == "PRODUCTION_READY"
    assert data["profile_count"] == 2
    assert data["profiles"][0]["market_regime"] == "RANGE"
    assert data["profiles"][0]["signal_context"] == "MEAN_REVERSION"
    assert data["profiles"][1]["market_regime"] == "TREND"
    assert data["architecture"]["validation_before_production_readiness"] is True
    assert data["architecture"]["live_execution_allowed"] is False


def test_production_readiness_calculates_score_deterministically():
    data = run_production_milestone_f_production_readiness(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "validation_score": 0.799536,
                "approved_runtime_weight": 0.500964,
                "evidence_quality": 0.892,
                "data_quality": 0.90,
                "knowledge_quality": 0.90,
                "explainability_score": 0.86,
                "runtime_stability": 0.88,
                "validation_sample_quality": 0.92,
                "validation_consistency": 0.87,
                "validation_risk": 0.12,
                "deployment_control_quality": 0.91,
                "monitoring_quality": 0.89,
                "rollback_readiness": 0.86,
            }
        ]
    )

    profile = data["profiles"][0]

    assert data["status"] == "PRODUCTION_READY"
    assert profile["operational_quality"] == 0.888
    assert profile["readiness_evidence_quality"] == 0.8898
    assert profile["production_readiness_score"] == 0.785329
    assert profile["production_runtime_weight"] == 0.393422
    assert profile["readiness_state"] == "PRODUCTION_READY"


def test_production_readiness_requires_review_for_low_monitoring_quality():
    data = run_production_milestone_f_production_readiness(
        [
            {
                "market_regime": "expansion",
                "signal_context": "momentum",
                "validation_score": 0.80,
                "approved_runtime_weight": 0.50,
                "evidence_quality": 0.84,
                "data_quality": 0.84,
                "knowledge_quality": 0.82,
                "explainability_score": 0.80,
                "runtime_stability": 0.82,
                "validation_sample_quality": 0.83,
                "validation_consistency": 0.82,
                "deployment_control_quality": 0.82,
                "monitoring_quality": 0.40,
                "rollback_readiness": 0.82,
            }
        ]
    )

    assert data["status"] == "PRODUCTION_READINESS_REVIEW_REQUIRED"
    assert data["decision"]["review_profile_count"] == 1
    assert data["profiles"][0]["readiness_state"] == "OPERATIONAL_REVIEW_REQUIRED"


def test_production_readiness_observation_normalizes_percent_values():
    observation = ProductionReadinessObservation.from_mapping(
        {
            "market_regime": "range",
            "signal_context": "wait",
            "validation_score": 82,
            "approved_runtime_weight": 60,
            "evidence_quality": 90,
            "data_quality": 88,
            "knowledge_quality": 84,
            "explainability_score": 91,
            "runtime_stability": 85,
            "validation_sample_quality": 89,
            "validation_consistency": 83,
            "validation_risk": 20,
            "deployment_control_quality": 92,
            "monitoring_quality": 86,
            "rollback_readiness": 81,
        }
    )

    assert observation.market_regime == "RANGE"
    assert observation.validation_score == 0.82
    assert observation.approved_runtime_weight == 0.60
    assert observation.evidence_quality == 0.90
    assert observation.data_quality == 0.88
    assert observation.knowledge_quality == 0.84
    assert observation.explainability_score == 0.91
    assert observation.runtime_stability == 0.85
    assert observation.validation_sample_quality == 0.89
    assert observation.validation_consistency == 0.83
    assert observation.validation_risk == 0.20
    assert observation.deployment_control_quality == 0.92
    assert observation.monitoring_quality == 0.86
    assert observation.rollback_readiness == 0.81
