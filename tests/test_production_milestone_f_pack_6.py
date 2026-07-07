from afip.runtime.production_milestone_f_runtime_adaptation_runtime import (
    run_production_milestone_f_runtime_adaptation,
)
from afip.runtime_adaptation import RuntimeAdaptationObservation, RuntimeAdaptationRuntime


def test_runtime_adaptation_blocks_records_without_market_regime():
    data = RuntimeAdaptationRuntime().run(
        [
            {
                "signal_context": "breakout",
                "proposed_strategy_weight": 0.62,
                "current_runtime_weight": 0.50,
                "evolution_pressure": 0.82,
                "evidence_quality": 0.90,
                "data_quality": 0.90,
                "knowledge_quality": 0.90,
                "stability_score": 0.88,
            }
        ]
    ).as_dict()

    assert data["status"] == "RUNTIME_ADAPTATION_BLOCKED"
    assert data["decision"]["invalid_market_regime_count"] == 1
    assert data["architecture"]["market_regime_before_signal_context"] is True


def test_runtime_adaptation_waits_for_strategy_evolution():
    data = run_production_milestone_f_runtime_adaptation([])

    assert data["status"] == "RUNTIME_ADAPTATION_WAIT"
    assert data["ready"] is False
    assert data["decision"]["reason"] == "strategy_evolution_required"


def test_runtime_adaptation_orders_by_regime_before_signal_context():
    data = run_production_milestone_f_runtime_adaptation(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "proposed_strategy_weight": 0.60,
                "current_runtime_weight": 0.50,
                "evolution_pressure": 0.80,
                "evidence_quality": 0.90,
                "data_quality": 0.90,
                "knowledge_quality": 0.90,
                "stability_score": 0.90,
            },
            {
                "market_regime": "range",
                "signal_context": "mean_reversion",
                "proposed_strategy_weight": 0.52,
                "current_runtime_weight": 0.50,
                "evolution_pressure": 0.62,
                "evidence_quality": 0.80,
                "data_quality": 0.82,
                "knowledge_quality": 0.80,
                "stability_score": 0.78,
            },
        ]
    )

    assert data["status"] == "RUNTIME_ADAPTATION_READY"
    assert data["profile_count"] == 2
    assert data["profiles"][0]["market_regime"] == "RANGE"
    assert data["profiles"][0]["signal_context"] == "MEAN_REVERSION"
    assert data["profiles"][1]["market_regime"] == "TREND"
    assert data["architecture"]["runtime_plan_write"] is False


def test_runtime_adaptation_calculates_plan_deterministically():
    data = run_production_milestone_f_runtime_adaptation(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "proposed_strategy_weight": 0.60,
                "current_runtime_weight": 0.50,
                "evolution_pressure": 0.80,
                "evidence_quality": 0.90,
                "data_quality": 0.90,
                "knowledge_quality": 0.90,
                "stability_score": 0.90,
                "execution_cost": 0.10,
            }
        ]
    )

    profile = data["profiles"][0]

    assert data["status"] == "RUNTIME_ADAPTATION_READY"
    assert profile["adaptation_quality"] == 0.9
    assert profile["adaptation_strength"] == 0.83025
    assert profile["planned_runtime_weight"] == 0.583025
    assert profile["runtime_weight_delta"] == 0.083025
    assert profile["adaptation_state"] == "PLAN_WEIGHT_INCREASE"


def test_runtime_adaptation_requires_review_for_low_stability():
    data = run_production_milestone_f_runtime_adaptation(
        [
            {
                "market_regime": "expansion",
                "signal_context": "momentum",
                "proposed_strategy_weight": 0.62,
                "current_runtime_weight": 0.50,
                "evolution_pressure": 0.80,
                "evidence_quality": 0.84,
                "data_quality": 0.82,
                "knowledge_quality": 0.82,
                "stability_score": 0.40,
            }
        ]
    )

    assert data["status"] == "RUNTIME_ADAPTATION_REVIEW_REQUIRED"
    assert data["decision"]["review_profile_count"] == 1
    assert data["profiles"][0]["adaptation_state"] == "RUNTIME_REVIEW_REQUIRED"


def test_runtime_adaptation_observation_normalizes_percent_values():
    observation = RuntimeAdaptationObservation.from_mapping(
        {
            "market_regime": "range",
            "signal_context": "wait",
            "proposed_strategy_weight": 60,
            "current_runtime_weight": 55,
            "evolution_pressure": 80,
            "evidence_quality": 90,
            "data_quality": 85,
            "knowledge_quality": 82,
            "stability_score": 75,
            "execution_cost": 20,
        }
    )

    assert observation.market_regime == "RANGE"
    assert observation.proposed_strategy_weight == 0.60
    assert observation.current_runtime_weight == 0.55
    assert observation.evolution_pressure == 0.80
    assert observation.evidence_quality == 0.90
    assert observation.data_quality == 0.85
    assert observation.knowledge_quality == 0.82
    assert observation.stability_score == 0.75
    assert observation.execution_cost == 0.20
