from afip.market_memory import (
    MarketMemoryObservation,
    MarketMemoryPolicy,
    MarketMemoryProfile,
    MarketMemoryRepository,
    MarketMemoryRuntime,
)
from afip.runtime.production_milestone_e_market_memory_runtime import (
    ProductionMilestoneEMarketMemoryRuntime,
)


def _ready_observations():
    return [
        {
            "market_regime": "trend expansion",
            "memory_pattern": "breakout continuation",
            "direction": "buy",
            "sample_count": 12,
            "similarity_score": 72,
            "recurrence_score": 66,
            "outcome_consistency": 68,
            "context_age_score": 74,
            "execution_cost_score": 65,
            "favorable_outcome_rate": 70,
            "trace_id": "mem-001",
        },
        {
            "regime": "TREND_EXPANSION",
            "pattern": "BREAKOUT_CONTINUATION",
            "bias": "BUY",
            "samples": 14,
            "similarity": 76,
            "recurrence": 64,
            "consistency": 70,
            "age_score": 72,
            "cost_score": 67,
            "outcome_rate": 72,
            "trace": "mem-002",
        },
    ]


def test_market_memory_observation_normalizes_market_regime_first_key():
    observation = MarketMemoryObservation.from_mapping(
        {
            "regime": "trend expansion",
            "pattern": "breakout continuation",
            "bias": "buy",
            "samples": 5,
            "similarity": 70,
            "recurrence": 60,
            "consistency": 65,
            "age_score": 70,
            "cost_score": 60,
            "outcome_rate": 67,
            "trace": "mem-a",
        }
    )

    assert observation.market_regime == "TREND_EXPANSION"
    assert observation.regime_memory_key == "TREND_EXPANSION:BREAKOUT_CONTINUATION:BUY"


def test_market_memory_observation_blocks_missing_traceability():
    observation = MarketMemoryObservation.from_mapping(
        {
            "market_regime": "TREND_EXPANSION",
            "memory_pattern": "BREAKOUT_CONTINUATION",
            "direction": "BUY",
            "sample_count": 5,
            "similarity_score": 70,
            "recurrence_score": 60,
            "outcome_consistency": 65,
            "context_age_score": 70,
            "execution_cost_score": 60,
            "favorable_outcome_rate": 67,
        }
    )

    assert observation.is_usable is False


def test_market_memory_repository_groups_by_market_regime_before_pattern():
    repository = MarketMemoryRepository(
        _ready_observations()
        + [
            {
                "market_regime": "range compression",
                "memory_pattern": "mean reversion",
                "direction": "sell",
                "sample_count": 25,
                "similarity_score": 80,
                "recurrence_score": 72,
                "outcome_consistency": 75,
                "context_age_score": 76,
                "execution_cost_score": 70,
                "favorable_outcome_rate": 74,
                "trace_id": "mem-003",
            }
        ]
    )

    keys = [profile.profile_key for profile in repository.build_profiles()]
    assert keys == ["RANGE_COMPRESSION:MEAN_REVERSION:SELL", "TREND_EXPANSION:BREAKOUT_CONTINUATION:BUY"]


def test_market_memory_profile_uses_data_derived_metrics():
    profile = MarketMemoryRepository(_ready_observations()).build_profiles()[0]

    assert profile.sample_count == 26
    assert profile.average_similarity_score == 74.0
    assert profile.average_recurrence_score == 65.0
    assert profile.favorable_outcome_rate == 71.0
    assert profile.memory_edge_score == 70.15


def test_market_memory_profile_requires_sufficient_samples():
    profile = MarketMemoryProfile.from_observations(
        (
            MarketMemoryObservation.from_mapping(
                {
                    **_ready_observations()[0],
                    "sample_count": 2,
                }
            ),
        )
    )

    assert profile.is_ready is False


def test_market_memory_profile_blocks_low_execution_cost_quality():
    profile = MarketMemoryRepository(
        [{**item, "execution_cost_score": 20} for item in _ready_observations()]
    ).build_profiles()[0]

    assert profile.is_ready is False


def test_market_memory_policy_waits_for_empty_profiles():
    decision = MarketMemoryPolicy().decide(())

    assert decision.status == "MARKET_MEMORY_WAIT"
    assert decision.action == "WAIT"


def test_market_memory_policy_selects_strongest_ready_profile():
    profiles = MarketMemoryRepository(
        _ready_observations()
        + [
            {
                "market_regime": "trend expansion",
                "memory_pattern": "pullback continuation",
                "direction": "buy",
                "sample_count": 30,
                "similarity_score": 85,
                "recurrence_score": 80,
                "outcome_consistency": 82,
                "context_age_score": 78,
                "execution_cost_score": 75,
                "favorable_outcome_rate": 80,
                "trace_id": "mem-004",
            }
        ]
    ).build_profiles()

    decision = MarketMemoryPolicy().decide(profiles)

    assert decision.status == "MARKET_MEMORY_READY"
    assert decision.selected_profile_key == "TREND_EXPANSION:PULLBACK_CONTINUATION:BUY"


def test_market_memory_runtime_builds_ready_report():
    report = MarketMemoryRuntime().run(_ready_observations())

    assert report.status == "MARKET_MEMORY_READY"
    assert report.action == "USE_MARKET_MEMORY_CONTEXT"
    assert report.active_market_regime == "TREND_EXPANSION"
    assert report.selected_memory_pattern == "BREAKOUT_CONTINUATION"
    assert report.is_ready is True


def test_market_memory_runtime_handles_empty_observations():
    report = MarketMemoryRuntime().run([])

    assert report.status == "MARKET_MEMORY_WAIT"
    assert report.profile_count == 0
    assert report.is_ready is False


def test_production_milestone_e_market_memory_runtime_is_deterministic():
    runtime = ProductionMilestoneEMarketMemoryRuntime()

    first = runtime.run(_ready_observations())
    second = runtime.run(list(reversed(_ready_observations())))

    assert first == second
