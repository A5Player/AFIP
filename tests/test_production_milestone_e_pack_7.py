from afip.portfolio_intelligence import (
    PortfolioObservation,
    PortfolioPolicy,
    PortfolioProfile,
    PortfolioRepository,
    PortfolioRuntime,
)
from afip.runtime.production_milestone_e_portfolio_intelligence_runtime import (
    ProductionMilestoneEPortfolioIntelligenceRuntime,
)


def _ready_observations():
    return [
        {
            "market_regime": "trend expansion",
            "portfolio_scope": "gold portfolio",
            "direction": "buy",
            "sample_count": 12,
            "exposure_score": 68,
            "correlation_score": 34,
            "risk_budget_utilization": 42,
            "diversification_score": 72,
            "portfolio_return_score": 74,
            "drawdown_pressure": 18,
            "execution_cost_score": 20,
            "trace_id": "pi-001",
        },
        {
            "regime": "TREND_EXPANSION",
            "scope": "GOLD_PORTFOLIO",
            "bias": "BUY",
            "samples": 14,
            "exposure": 72,
            "correlation": 36,
            "risk_budget": 44,
            "diversification": 74,
            "return_score": 76,
            "drawdown": 16,
            "cost_score": 18,
            "trace": "pi-002",
        },
    ]


def test_portfolio_observation_normalizes_market_regime_first_key():
    observation = PortfolioObservation.from_mapping(
        {
            "regime": "trend expansion",
            "scope": "gold portfolio",
            "bias": "buy",
            "samples": 5,
            "exposure": 70,
            "correlation": 35,
            "risk_budget": 44,
            "diversification": 73,
            "return_score": 75,
            "drawdown": 17,
            "cost_score": 19,
            "trace": "pi-a",
        }
    )

    assert observation.market_regime == "TREND_EXPANSION"
    assert observation.portfolio_key == "TREND_EXPANSION:GOLD_PORTFOLIO:BUY"


def test_portfolio_observation_blocks_missing_traceability():
    observation = PortfolioObservation.from_mapping(
        {
            "market_regime": "TREND_EXPANSION",
            "portfolio_scope": "GOLD_PORTFOLIO",
            "direction": "BUY",
            "sample_count": 5,
            "exposure_score": 70,
            "correlation_score": 35,
            "risk_budget_utilization": 44,
            "diversification_score": 73,
            "portfolio_return_score": 75,
            "drawdown_pressure": 17,
            "execution_cost_score": 19,
        }
    )

    assert observation.is_usable is False


def test_portfolio_repository_groups_by_market_regime_before_scope():
    repository = PortfolioRepository(
        _ready_observations()
        + [
            {
                "market_regime": "range compression",
                "portfolio_scope": "gold portfolio",
                "direction": "sell",
                "sample_count": 25,
                "exposure_score": 60,
                "correlation_score": 45,
                "risk_budget_utilization": 48,
                "diversification_score": 68,
                "portfolio_return_score": 66,
                "drawdown_pressure": 20,
                "execution_cost_score": 22,
                "trace_id": "pi-003",
            }
        ]
    )

    keys = [profile.profile_key for profile in repository.build_profiles()]
    assert keys == ["RANGE_COMPRESSION:GOLD_PORTFOLIO:SELL", "TREND_EXPANSION:GOLD_PORTFOLIO:BUY"]


def test_portfolio_profile_uses_data_derived_metrics():
    profile = PortfolioRepository(_ready_observations()).build_profiles()[0]

    assert profile.sample_count == 26
    assert profile.average_exposure_score == 70.0
    assert profile.average_correlation_score == 35.0
    assert profile.average_risk_budget_utilization == 43.0
    assert profile.average_drawdown_pressure == 17.0
    assert profile.portfolio_resilience_score == 75.3


def test_portfolio_profile_requires_sufficient_samples():
    profile = PortfolioProfile.from_observations(
        (
            PortfolioObservation.from_mapping(
                {
                    **_ready_observations()[0],
                    "sample_count": 2,
                }
            ),
        )
    )

    assert profile.is_ready is False


def test_portfolio_profile_blocks_high_correlation():
    profile = PortfolioRepository(
        [{**item, "correlation_score": 88, "correlation": 88} for item in _ready_observations()]
    ).build_profiles()[0]

    assert profile.is_ready is False


def test_portfolio_policy_waits_for_empty_profiles():
    decision = PortfolioPolicy().decide(())

    assert decision.status == "PORTFOLIO_INTELLIGENCE_WAIT"
    assert decision.action == "WAIT"


def test_portfolio_policy_selects_strongest_ready_profile():
    profiles = PortfolioRepository(
        _ready_observations()
        + [
            {
                "market_regime": "trend expansion",
                "portfolio_scope": "hedged portfolio",
                "direction": "buy",
                "sample_count": 30,
                "exposure_score": 66,
                "correlation_score": 22,
                "risk_budget_utilization": 36,
                "diversification_score": 82,
                "portfolio_return_score": 80,
                "drawdown_pressure": 10,
                "execution_cost_score": 15,
                "trace_id": "pi-004",
            }
        ]
    ).build_profiles()

    decision = PortfolioPolicy().decide(profiles)

    assert decision.status == "PORTFOLIO_INTELLIGENCE_READY"
    assert decision.selected_profile_key == "TREND_EXPANSION:HEDGED_PORTFOLIO:BUY"


def test_portfolio_runtime_builds_ready_report():
    report = PortfolioRuntime().run(_ready_observations())

    assert report.status == "PORTFOLIO_INTELLIGENCE_READY"
    assert report.action == "APPLY_PORTFOLIO_CONTEXT"
    assert report.active_market_regime == "TREND_EXPANSION"
    assert report.selected_portfolio_scope == "GOLD_PORTFOLIO"
    assert report.is_ready is True


def test_portfolio_runtime_handles_empty_observations():
    report = PortfolioRuntime().run([])

    assert report.status == "PORTFOLIO_INTELLIGENCE_WAIT"
    assert report.profile_count == 0
    assert report.is_ready is False


def test_production_milestone_e_portfolio_intelligence_runtime_is_deterministic():
    runtime = ProductionMilestoneEPortfolioIntelligenceRuntime()

    first = runtime.run(_ready_observations())
    second = runtime.run(list(reversed(_ready_observations())))

    assert first == second
