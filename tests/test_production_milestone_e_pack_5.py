from afip.dynamic_weight import (
    DynamicWeightObservation,
    DynamicWeightPolicy,
    DynamicWeightProfile,
    DynamicWeightRepository,
    DynamicWeightRuntime,
)
from afip.runtime.production_milestone_e_dynamic_weight_runtime import (
    ProductionMilestoneEDynamicWeightRuntime,
)


def _ready_observations():
    return [
        {
            "market_regime": "trend expansion",
            "intelligence_name": "regime intelligence",
            "direction": "buy",
            "sample_count": 12,
            "contribution_score": 74,
            "accuracy_rate": 70,
            "stability_score": 72,
            "recency_score": 76,
            "execution_cost_score": 66,
            "conflict_score": 18,
            "trace_id": "dw-001",
        },
        {
            "regime": "TREND_EXPANSION",
            "engine": "REGIME_INTELLIGENCE",
            "bias": "BUY",
            "samples": 14,
            "contribution": 78,
            "realized_accuracy_rate": 72,
            "weight_stability_score": 74,
            "freshness_score": 78,
            "cost_score": 68,
            "opposition_score": 16,
            "trace": "dw-002",
        },
    ]


def test_dynamic_weight_observation_normalizes_market_regime_first_key():
    observation = DynamicWeightObservation.from_mapping(
        {
            "regime": "trend expansion",
            "engine": "regime intelligence",
            "bias": "buy",
            "samples": 5,
            "contribution": 70,
            "realized_accuracy_rate": 66,
            "weight_stability_score": 71,
            "freshness_score": 73,
            "cost_score": 60,
            "opposition_score": 20,
            "trace": "dw-a",
        }
    )

    assert observation.market_regime == "TREND_EXPANSION"
    assert observation.regime_weight_key == "TREND_EXPANSION:REGIME_INTELLIGENCE:BUY"


def test_dynamic_weight_observation_blocks_missing_traceability():
    observation = DynamicWeightObservation.from_mapping(
        {
            "market_regime": "TREND_EXPANSION",
            "intelligence_name": "REGIME_INTELLIGENCE",
            "direction": "BUY",
            "sample_count": 5,
            "contribution_score": 70,
            "accuracy_rate": 66,
            "stability_score": 71,
            "recency_score": 73,
            "execution_cost_score": 60,
            "conflict_score": 20,
        }
    )

    assert observation.is_usable is False


def test_dynamic_weight_repository_groups_by_market_regime_before_intelligence():
    repository = DynamicWeightRepository(
        _ready_observations()
        + [
            {
                "market_regime": "range compression",
                "intelligence_name": "session intelligence",
                "direction": "sell",
                "sample_count": 25,
                "contribution_score": 69,
                "accuracy_rate": 72,
                "stability_score": 75,
                "recency_score": 74,
                "execution_cost_score": 70,
                "conflict_score": 15,
                "trace_id": "dw-003",
            }
        ]
    )

    keys = [profile.profile_key for profile in repository.build_profiles()]
    assert keys == ["RANGE_COMPRESSION:SESSION_INTELLIGENCE:SELL", "TREND_EXPANSION:REGIME_INTELLIGENCE:BUY"]


def test_dynamic_weight_profile_uses_data_derived_metrics():
    profile = DynamicWeightRepository(_ready_observations()).build_profiles()[0]

    assert profile.sample_count == 26
    assert profile.average_contribution_score == 76.0
    assert profile.average_accuracy_rate == 71.0
    assert profile.average_conflict_score == 17.0
    assert profile.normalized_weight_score == 73.9


def test_dynamic_weight_profile_requires_sufficient_samples():
    profile = DynamicWeightProfile.from_observations(
        (
            DynamicWeightObservation.from_mapping(
                {
                    **_ready_observations()[0],
                    "sample_count": 2,
                }
            ),
        )
    )

    assert profile.is_ready is False


def test_dynamic_weight_profile_blocks_high_conflict():
    profile = DynamicWeightRepository(
        [{**item, "conflict_score": 55} for item in _ready_observations()]
    ).build_profiles()[0]

    assert profile.is_ready is False


def test_dynamic_weight_policy_waits_for_empty_profiles():
    decision = DynamicWeightPolicy().decide(())

    assert decision.status == "DYNAMIC_WEIGHT_WAIT"
    assert decision.action == "WAIT"


def test_dynamic_weight_policy_selects_strongest_ready_profile():
    profiles = DynamicWeightRepository(
        _ready_observations()
        + [
            {
                "market_regime": "trend expansion",
                "intelligence_name": "memory intelligence",
                "direction": "buy",
                "sample_count": 30,
                "contribution_score": 82,
                "accuracy_rate": 81,
                "stability_score": 80,
                "recency_score": 79,
                "execution_cost_score": 75,
                "conflict_score": 10,
                "trace_id": "dw-004",
            }
        ]
    ).build_profiles()

    decision = DynamicWeightPolicy().decide(profiles)

    assert decision.status == "DYNAMIC_WEIGHT_READY"
    assert decision.selected_profile_key == "TREND_EXPANSION:MEMORY_INTELLIGENCE:BUY"


def test_dynamic_weight_runtime_builds_ready_report():
    report = DynamicWeightRuntime().run(_ready_observations())

    assert report.status == "DYNAMIC_WEIGHT_READY"
    assert report.action == "APPLY_DYNAMIC_WEIGHT"
    assert report.active_market_regime == "TREND_EXPANSION"
    assert report.selected_intelligence_name == "REGIME_INTELLIGENCE"
    assert report.is_ready is True


def test_dynamic_weight_runtime_handles_empty_observations():
    report = DynamicWeightRuntime().run([])

    assert report.status == "DYNAMIC_WEIGHT_WAIT"
    assert report.profile_count == 0
    assert report.is_ready is False


def test_production_milestone_e_dynamic_weight_runtime_is_deterministic():
    runtime = ProductionMilestoneEDynamicWeightRuntime()

    first = runtime.run(_ready_observations())
    second = runtime.run(list(reversed(_ready_observations())))

    assert first == second
