from afip.milestone_f_complete import MilestoneFCompletionObservation, MilestoneFCompletionRuntime
from afip.runtime.production_milestone_f_complete_runtime import run_production_milestone_f_complete


def test_milestone_f_completion_blocks_records_without_market_regime():
    data = MilestoneFCompletionRuntime().run(
        [
            {
                "signal_context": "continuation",
                "production_readiness_score": 0.80,
                "production_runtime_weight": 0.40,
                "readiness_evidence_quality": 0.88,
                "data_quality": 0.90,
                "knowledge_quality": 0.88,
                "strategy_quality": 0.86,
                "runtime_stability": 0.88,
                "validation_quality": 0.87,
                "monitoring_quality": 0.86,
                "rollback_readiness": 0.84,
                "documentation_quality": 0.90,
                "handoff_quality": 0.90,
            }
        ]
    ).as_dict()

    assert data["status"] == "MILESTONE_F_COMPLETION_BLOCKED"
    assert data["decision"]["invalid_market_regime_count"] == 1
    assert data["architecture"]["market_regime_before_signal_context"] is True


def test_milestone_f_completion_waits_for_production_readiness():
    data = run_production_milestone_f_complete([])

    assert data["status"] == "MILESTONE_F_COMPLETION_WAIT"
    assert data["complete"] is False
    assert data["decision"]["reason"] == "production_readiness_required"


def test_milestone_f_completion_orders_by_regime_before_signal_context():
    data = run_production_milestone_f_complete(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "production_readiness_score": 0.80,
                "production_runtime_weight": 0.40,
                "readiness_evidence_quality": 0.88,
                "data_quality": 0.90,
                "knowledge_quality": 0.88,
                "strategy_quality": 0.86,
                "runtime_stability": 0.88,
                "validation_quality": 0.87,
                "monitoring_quality": 0.86,
                "rollback_readiness": 0.84,
                "documentation_quality": 0.90,
                "handoff_quality": 0.90,
            },
            {
                "market_regime": "range",
                "signal_context": "mean_reversion",
                "production_readiness_score": 0.77,
                "production_runtime_weight": 0.36,
                "readiness_evidence_quality": 0.84,
                "data_quality": 0.84,
                "knowledge_quality": 0.83,
                "strategy_quality": 0.82,
                "runtime_stability": 0.80,
                "validation_quality": 0.80,
                "monitoring_quality": 0.81,
                "rollback_readiness": 0.80,
                "documentation_quality": 0.86,
                "handoff_quality": 0.86,
            },
        ]
    )

    assert data["status"] == "MILESTONE_F_COMPLETE"
    assert data["profile_count"] == 2
    assert data["profiles"][0]["market_regime"] == "RANGE"
    assert data["profiles"][0]["signal_context"] == "MEAN_REVERSION"
    assert data["profiles"][1]["market_regime"] == "TREND"
    assert data["architecture"]["production_readiness_before_milestone_completion"] is True
    assert data["architecture"]["live_execution_allowed"] is False


def test_milestone_f_completion_calculates_score_deterministically():
    data = run_production_milestone_f_complete(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "production_readiness_score": 0.803,
                "production_runtime_weight": 0.393,
                "readiness_evidence_quality": 0.8898,
                "data_quality": 0.90,
                "knowledge_quality": 0.90,
                "strategy_quality": 0.88,
                "runtime_stability": 0.88,
                "validation_quality": 0.87,
                "monitoring_quality": 0.89,
                "rollback_readiness": 0.86,
                "documentation_quality": 0.92,
                "handoff_quality": 0.91,
                "completion_risk": 0.10,
            }
        ]
    )

    profile = data["profiles"][0]

    assert data["status"] == "MILESTONE_F_COMPLETE"
    assert profile["operational_closure_quality"] == 0.89
    assert profile["milestone_evidence_quality"] == 0.88846
    assert profile["milestone_completion_score"] == 0.796269
    assert profile["final_runtime_weight"] == 0.312934
    assert profile["completion_state"] == "MILESTONE_F_COMPLETE"


def test_milestone_f_completion_requires_review_for_low_handoff_quality():
    data = run_production_milestone_f_complete(
        [
            {
                "market_regime": "expansion",
                "signal_context": "momentum",
                "production_readiness_score": 0.80,
                "production_runtime_weight": 0.40,
                "readiness_evidence_quality": 0.84,
                "data_quality": 0.84,
                "knowledge_quality": 0.82,
                "strategy_quality": 0.80,
                "runtime_stability": 0.82,
                "validation_quality": 0.82,
                "monitoring_quality": 0.82,
                "rollback_readiness": 0.82,
                "documentation_quality": 0.82,
                "handoff_quality": 0.40,
            }
        ]
    )

    assert data["status"] == "MILESTONE_F_COMPLETION_REVIEW_REQUIRED"
    assert data["decision"]["review_profile_count"] == 1
    assert data["profiles"][0]["completion_state"] == "DOCUMENTATION_REVIEW_REQUIRED"


def test_milestone_f_completion_observation_normalizes_percent_values():
    observation = MilestoneFCompletionObservation.from_mapping(
        {
            "market_regime": "range",
            "signal_context": "wait",
            "production_readiness_score": 82,
            "production_runtime_weight": 60,
            "readiness_evidence_quality": 90,
            "data_quality": 88,
            "knowledge_quality": 84,
            "strategy_quality": 91,
            "runtime_stability": 85,
            "validation_quality": 89,
            "monitoring_quality": 86,
            "rollback_readiness": 81,
            "documentation_quality": 92,
            "handoff_quality": 87,
            "completion_risk": 20,
        }
    )

    assert observation.market_regime == "RANGE"
    assert observation.production_readiness_score == 0.82
    assert observation.production_runtime_weight == 0.60
    assert observation.readiness_evidence_quality == 0.90
    assert observation.data_quality == 0.88
    assert observation.knowledge_quality == 0.84
    assert observation.strategy_quality == 0.91
    assert observation.runtime_stability == 0.85
    assert observation.validation_quality == 0.89
    assert observation.monitoring_quality == 0.86
    assert observation.rollback_readiness == 0.81
    assert observation.documentation_quality == 0.92
    assert observation.handoff_quality == 0.87
    assert observation.completion_risk == 0.20
