from afip.runtime.production_milestone_f_strategy_evolution_runtime import (
    run_production_milestone_f_strategy_evolution,
)
from afip.strategy_evolution import StrategyEvolutionObservation, StrategyEvolutionRuntime


def test_strategy_evolution_blocks_records_without_market_regime():
    data = StrategyEvolutionRuntime().run(
        [
            {
                "signal_context": "breakout",
                "experience_score": 0.90,
                "expectancy": 0.40,
                "sample_count": 6,
                "positive_rate": 0.82,
                "data_quality": 0.90,
                "knowledge_quality": 0.88,
                "reliability_score": 0.86,
            }
        ]
    ).as_dict()

    assert data["status"] == "STRATEGY_EVOLUTION_BLOCKED"
    assert data["decision"]["invalid_market_regime_count"] == 1
    assert data["architecture"]["market_regime_before_signal_context"] is True


def test_strategy_evolution_waits_for_experience_knowledge():
    data = run_production_milestone_f_strategy_evolution([])

    assert data["status"] == "STRATEGY_EVOLUTION_WAIT"
    assert data["ready"] is False
    assert data["decision"]["reason"] == "experience_knowledge_required"


def test_strategy_evolution_groups_by_regime_before_signal_context():
    data = run_production_milestone_f_strategy_evolution(
        [
            {
                "market_regime": "trend",
                "signal_context": "breakout",
                "experience_score": 0.88,
                "expectancy": 0.50,
                "sample_count": 4,
                "positive_rate": 0.80,
                "data_quality": 0.92,
                "knowledge_quality": 0.90,
                "reliability_score": 0.89,
            },
            {
                "market_regime": "range",
                "signal_context": "mean_reversion",
                "experience_score": 0.64,
                "expectancy": 0.10,
                "sample_count": 3,
                "positive_rate": 0.58,
                "data_quality": 0.76,
                "knowledge_quality": 0.75,
                "reliability_score": 0.72,
            },
        ]
    )

    assert data["status"] == "STRATEGY_EVOLUTION_READY"
    assert data["profile_count"] == 2
    assert data["profiles"][0]["market_regime"] == "RANGE"
    assert data["profiles"][0]["signal_context"] == "MEAN_REVERSION"
    assert data["profiles"][1]["market_regime"] == "TREND"
    assert data["architecture"]["strategy_runtime_write"] is False


def test_strategy_evolution_calculates_candidate_weight_deterministically():
    data = run_production_milestone_f_strategy_evolution(
        [
            {
                "market_regime": "trend",
                "signal_context": "continuation",
                "experience_score": 0.90,
                "expectancy": 0.60,
                "sample_count": 5,
                "positive_rate": 0.80,
                "data_quality": 0.90,
                "knowledge_quality": 0.90,
                "reliability_score": 0.90,
                "current_strategy_weight": 0.50,
            }
        ]
    )

    profile = data["profiles"][0]

    assert data["status"] == "STRATEGY_EVOLUTION_READY"
    assert profile["evolution_pressure"] == 0.855
    assert profile["proposed_strategy_weight"] == 0.571
    assert profile["weight_adjustment"] == 0.071
    assert profile["evolution_state"] == "INCREASE_STRATEGY_WEIGHT"


def test_strategy_evolution_requires_review_for_low_evidence_quality():
    data = run_production_milestone_f_strategy_evolution(
        [
            {
                "market_regime": "expansion",
                "signal_context": "momentum",
                "experience_score": 0.78,
                "expectancy": 0.30,
                "sample_count": 2,
                "positive_rate": 0.70,
                "data_quality": 0.40,
                "knowledge_quality": 0.84,
                "reliability_score": 0.82,
            }
        ]
    )

    assert data["status"] == "STRATEGY_EVOLUTION_REVIEW_REQUIRED"
    assert data["decision"]["review_profile_count"] == 1
    assert data["profiles"][0]["evolution_state"] == "EVIDENCE_REVIEW_REQUIRED"


def test_strategy_evolution_observation_normalizes_percent_values():
    observation = StrategyEvolutionObservation.from_mapping(
        {
            "market_regime": "range",
            "signal_context": "wait",
            "experience_score": 75,
            "expectancy": 20,
            "sample_count": 2,
            "positive_rate": 60,
            "data_quality": 90,
            "knowledge_quality": 85,
            "reliability_score": 80,
            "current_strategy_weight": 55,
        }
    )

    assert observation.market_regime == "RANGE"
    assert observation.experience_score == 0.75
    assert observation.expectancy == 0.20
    assert observation.positive_rate == 0.60
    assert observation.data_quality == 0.90
    assert observation.knowledge_quality == 0.85
    assert observation.reliability_score == 0.80
    assert observation.current_strategy_weight == 0.55
