from afip.adaptive_learning import (
    AdaptiveLearningObservation,
    AdaptiveLearningPolicy,
    AdaptiveLearningProfile,
    AdaptiveLearningRepository,
    AdaptiveLearningRuntime,
)
from afip.runtime.production_milestone_e_adaptive_learning_runtime import (
    ProductionMilestoneEAdaptiveLearningRuntime,
)


def _ready_observations():
    return [
        {
            "market_regime": "trend expansion",
            "learning_context": "breakout reinforcement",
            "direction": "buy",
            "sample_count": 12,
            "reinforcement_score": 72,
            "adaptation_score": 70,
            "forgetting_score": 18,
            "validation_score": 74,
            "stability_score": 76,
            "drift_risk_score": 20,
            "execution_cost_score": 22,
            "trace_id": "al-001",
        },
        {
            "regime": "TREND_EXPANSION",
            "context": "BREAKOUT_REINFORCEMENT",
            "bias": "BUY",
            "samples": 14,
            "reinforcement": 74,
            "adaptation": 72,
            "forgetting": 16,
            "validation": 76,
            "stability": 78,
            "drift_risk": 18,
            "cost_score": 20,
            "trace": "al-002",
        },
    ]


def test_adaptive_learning_observation_normalizes_market_regime_first_key():
    observation = AdaptiveLearningObservation.from_mapping(
        {
            "regime": "trend expansion",
            "context": "breakout reinforcement",
            "bias": "buy",
            "samples": 5,
            "reinforcement": 73,
            "adaptation": 71,
            "forgetting": 17,
            "validation": 75,
            "stability": 77,
            "drift_risk": 19,
            "cost_score": 21,
            "trace": "al-a",
        }
    )

    assert observation.market_regime == "TREND_EXPANSION"
    assert observation.learning_key == "TREND_EXPANSION:BREAKOUT_REINFORCEMENT:BUY"


def test_adaptive_learning_observation_blocks_missing_traceability():
    observation = AdaptiveLearningObservation.from_mapping(
        {
            "market_regime": "TREND_EXPANSION",
            "learning_context": "BREAKOUT_REINFORCEMENT",
            "direction": "BUY",
            "sample_count": 5,
            "reinforcement_score": 73,
            "adaptation_score": 71,
            "forgetting_score": 17,
            "validation_score": 75,
            "stability_score": 77,
            "drift_risk_score": 19,
            "execution_cost_score": 21,
        }
    )

    assert observation.is_usable is False


def test_adaptive_learning_repository_groups_by_market_regime_before_context():
    repository = AdaptiveLearningRepository(
        _ready_observations()
        + [
            {
                "market_regime": "range compression",
                "learning_context": "mean reversion refinement",
                "direction": "sell",
                "sample_count": 25,
                "reinforcement_score": 62,
                "adaptation_score": 66,
                "forgetting_score": 24,
                "validation_score": 64,
                "stability_score": 68,
                "drift_risk_score": 26,
                "execution_cost_score": 22,
                "trace_id": "al-003",
            }
        ]
    )

    keys = [profile.profile_key for profile in repository.build_profiles()]
    assert keys == ["RANGE_COMPRESSION:MEAN_REVERSION_REFINEMENT:SELL", "TREND_EXPANSION:BREAKOUT_REINFORCEMENT:BUY"]


def test_adaptive_learning_profile_uses_data_derived_metrics():
    profile = AdaptiveLearningRepository(_ready_observations()).build_profiles()[0]

    assert profile.sample_count == 26
    assert profile.average_reinforcement_score == 73.0
    assert profile.average_adaptation_score == 71.0
    assert profile.average_drift_risk_score == 19.0
    assert profile.average_execution_cost_score == 21.0
    assert profile.adaptive_learning_score == 76.2


def test_adaptive_learning_profile_requires_sufficient_samples():
    profile = AdaptiveLearningProfile.from_observations(
        (
            AdaptiveLearningObservation.from_mapping(
                {
                    **_ready_observations()[0],
                    "sample_count": 2,
                }
            ),
        )
    )

    assert profile.is_ready is False


def test_adaptive_learning_profile_blocks_high_drift_risk():
    profile = AdaptiveLearningRepository(
        [{**item, "drift_risk_score": 72, "drift_risk": 72} for item in _ready_observations()]
    ).build_profiles()[0]

    assert profile.is_ready is False


def test_adaptive_learning_policy_waits_for_empty_profiles():
    decision = AdaptiveLearningPolicy().decide(())

    assert decision.status == "ADAPTIVE_LEARNING_WAIT"
    assert decision.action == "WAIT"


def test_adaptive_learning_policy_selects_strongest_ready_profile():
    profiles = AdaptiveLearningRepository(
        _ready_observations()
        + [
            {
                "market_regime": "trend expansion",
                "learning_context": "continuation adaptation",
                "direction": "buy",
                "sample_count": 30,
                "reinforcement_score": 82,
                "adaptation_score": 80,
                "forgetting_score": 12,
                "validation_score": 84,
                "stability_score": 82,
                "drift_risk_score": 14,
                "execution_cost_score": 15,
                "trace_id": "al-004",
            }
        ]
    ).build_profiles()

    decision = AdaptiveLearningPolicy().decide(profiles)

    assert decision.status == "ADAPTIVE_LEARNING_READY"
    assert decision.selected_profile_key == "TREND_EXPANSION:CONTINUATION_ADAPTATION:BUY"


def test_adaptive_learning_runtime_builds_ready_report():
    report = AdaptiveLearningRuntime().run(_ready_observations())

    assert report.status == "ADAPTIVE_LEARNING_READY"
    assert report.action == "APPLY_ADAPTIVE_LEARNING"
    assert report.active_market_regime == "TREND_EXPANSION"
    assert report.selected_learning_context == "BREAKOUT_REINFORCEMENT"
    assert report.is_ready is True


def test_adaptive_learning_runtime_handles_empty_observations():
    report = AdaptiveLearningRuntime().run([])

    assert report.status == "ADAPTIVE_LEARNING_WAIT"
    assert report.profile_count == 0
    assert report.is_ready is False


def test_production_milestone_e_adaptive_learning_runtime_is_deterministic():
    runtime = ProductionMilestoneEAdaptiveLearningRuntime()

    first = runtime.run(_ready_observations())
    second = runtime.run(list(reversed(_ready_observations())))

    assert first == second
