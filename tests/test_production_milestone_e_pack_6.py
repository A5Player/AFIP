from afip.performance_attribution import (
    PerformanceAttributionObservation,
    PerformanceAttributionPolicy,
    PerformanceAttributionProfile,
    PerformanceAttributionRepository,
    PerformanceAttributionRuntime,
)
from afip.runtime.production_milestone_e_performance_attribution_runtime import (
    ProductionMilestoneEPerformanceAttributionRuntime,
)


def _ready_observations():
    return [
        {
            "market_regime": "trend expansion",
            "attribution_source": "decision intelligence",
            "direction": "buy",
            "sample_count": 12,
            "gross_pnl": 140,
            "net_pnl": 112,
            "contribution_score": 74,
            "decision_alignment_rate": 70,
            "execution_quality_score": 72,
            "drawdown_impact": 18,
            "trace_id": "pa-001",
        },
        {
            "regime": "TREND_EXPANSION",
            "component": "DECISION_INTELLIGENCE",
            "bias": "BUY",
            "samples": 14,
            "gross_profit": 160,
            "net_profit": 128,
            "contribution": 78,
            "alignment_rate": 72,
            "quality_score": 74,
            "drawdown": 16,
            "trace": "pa-002",
        },
    ]


def test_performance_attribution_observation_normalizes_market_regime_first_key():
    observation = PerformanceAttributionObservation.from_mapping(
        {
            "regime": "trend expansion",
            "component": "decision intelligence",
            "bias": "buy",
            "samples": 5,
            "gross_profit": 100,
            "net_profit": 78,
            "contribution": 70,
            "alignment_rate": 66,
            "quality_score": 71,
            "drawdown": 20,
            "trace": "pa-a",
        }
    )

    assert observation.market_regime == "TREND_EXPANSION"
    assert observation.attribution_key == "TREND_EXPANSION:DECISION_INTELLIGENCE:BUY"


def test_performance_attribution_observation_blocks_missing_traceability():
    observation = PerformanceAttributionObservation.from_mapping(
        {
            "market_regime": "TREND_EXPANSION",
            "attribution_source": "DECISION_INTELLIGENCE",
            "direction": "BUY",
            "sample_count": 5,
            "gross_pnl": 100,
            "net_pnl": 78,
            "contribution_score": 70,
            "decision_alignment_rate": 66,
            "execution_quality_score": 71,
            "drawdown_impact": 20,
        }
    )

    assert observation.is_usable is False


def test_performance_attribution_repository_groups_by_market_regime_before_source():
    repository = PerformanceAttributionRepository(
        _ready_observations()
        + [
            {
                "market_regime": "range compression",
                "attribution_source": "execution readiness",
                "direction": "sell",
                "sample_count": 25,
                "gross_pnl": 130,
                "net_pnl": 104,
                "contribution_score": 69,
                "decision_alignment_rate": 72,
                "execution_quality_score": 75,
                "drawdown_impact": 15,
                "trace_id": "pa-003",
            }
        ]
    )

    keys = [profile.profile_key for profile in repository.build_profiles()]
    assert keys == ["RANGE_COMPRESSION:EXECUTION_READINESS:SELL", "TREND_EXPANSION:DECISION_INTELLIGENCE:BUY"]


def test_performance_attribution_profile_uses_data_derived_metrics():
    profile = PerformanceAttributionRepository(_ready_observations()).build_profiles()[0]

    assert profile.sample_count == 26
    assert profile.total_gross_pnl == 300.0
    assert profile.total_net_pnl == 240.0
    assert profile.average_contribution_score == 76.0
    assert profile.average_drawdown_impact == 17.0
    assert profile.attribution_efficiency_score == 75.65


def test_performance_attribution_profile_requires_sufficient_samples():
    profile = PerformanceAttributionProfile.from_observations(
        (
            PerformanceAttributionObservation.from_mapping(
                {
                    **_ready_observations()[0],
                    "sample_count": 2,
                }
            ),
        )
    )

    assert profile.is_ready is False


def test_performance_attribution_profile_blocks_negative_net_pnl():
    profile = PerformanceAttributionRepository(
        [{**item, "net_pnl": -20, "net_profit": -20} for item in _ready_observations()]
    ).build_profiles()[0]

    assert profile.is_ready is False


def test_performance_attribution_policy_waits_for_empty_profiles():
    decision = PerformanceAttributionPolicy().decide(())

    assert decision.status == "PERFORMANCE_ATTRIBUTION_WAIT"
    assert decision.action == "WAIT"


def test_performance_attribution_policy_selects_strongest_ready_profile():
    profiles = PerformanceAttributionRepository(
        _ready_observations()
        + [
            {
                "market_regime": "trend expansion",
                "attribution_source": "execution readiness",
                "direction": "buy",
                "sample_count": 30,
                "gross_pnl": 190,
                "net_pnl": 171,
                "contribution_score": 82,
                "decision_alignment_rate": 81,
                "execution_quality_score": 80,
                "drawdown_impact": 10,
                "trace_id": "pa-004",
            }
        ]
    ).build_profiles()

    decision = PerformanceAttributionPolicy().decide(profiles)

    assert decision.status == "PERFORMANCE_ATTRIBUTION_READY"
    assert decision.selected_profile_key == "TREND_EXPANSION:EXECUTION_READINESS:BUY"


def test_performance_attribution_runtime_builds_ready_report():
    report = PerformanceAttributionRuntime().run(_ready_observations())

    assert report.status == "PERFORMANCE_ATTRIBUTION_READY"
    assert report.action == "APPLY_PERFORMANCE_ATTRIBUTION"
    assert report.active_market_regime == "TREND_EXPANSION"
    assert report.selected_attribution_source == "DECISION_INTELLIGENCE"
    assert report.is_ready is True


def test_performance_attribution_runtime_handles_empty_observations():
    report = PerformanceAttributionRuntime().run([])

    assert report.status == "PERFORMANCE_ATTRIBUTION_WAIT"
    assert report.profile_count == 0
    assert report.is_ready is False


def test_production_milestone_e_performance_attribution_runtime_is_deterministic():
    runtime = ProductionMilestoneEPerformanceAttributionRuntime()

    first = runtime.run(_ready_observations())
    second = runtime.run(list(reversed(_ready_observations())))

    assert first == second
