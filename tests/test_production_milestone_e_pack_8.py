from afip.macro_context import (
    MacroObservation,
    MacroPolicy,
    MacroProfile,
    MacroRepository,
    MacroRuntime,
)
from afip.runtime.production_milestone_e_macro_context_runtime import (
    ProductionMilestoneEMacroContextRuntime,
)


def _ready_observations():
    return [
        {
            "market_regime": "trend expansion",
            "macro_theme": "gold macro support",
            "direction": "buy",
            "sample_count": 12,
            "dxy_alignment_score": 74,
            "yield_alignment_score": 70,
            "inflation_surprise_score": 64,
            "labor_market_pressure": 22,
            "policy_rate_bias_score": 68,
            "news_risk_score": 24,
            "macro_consensus_score": 76,
            "execution_cost_score": 20,
            "trace_id": "mc-001",
        },
        {
            "regime": "TREND_EXPANSION",
            "theme": "GOLD_MACRO_SUPPORT",
            "bias": "BUY",
            "samples": 14,
            "dxy_alignment": 76,
            "yield_alignment": 72,
            "inflation_surprise": 66,
            "labor_pressure": 20,
            "policy_rate_bias": 70,
            "news_risk": 22,
            "macro_consensus": 78,
            "cost_score": 18,
            "trace": "mc-002",
        },
    ]


def test_macro_observation_normalizes_market_regime_first_key():
    observation = MacroObservation.from_mapping(
        {
            "regime": "trend expansion",
            "theme": "gold macro support",
            "bias": "buy",
            "samples": 5,
            "dxy_alignment": 75,
            "yield_alignment": 71,
            "inflation_surprise": 65,
            "labor_pressure": 21,
            "policy_rate_bias": 69,
            "news_risk": 23,
            "macro_consensus": 77,
            "cost_score": 19,
            "trace": "mc-a",
        }
    )

    assert observation.market_regime == "TREND_EXPANSION"
    assert observation.macro_key == "TREND_EXPANSION:GOLD_MACRO_SUPPORT:BUY"


def test_macro_observation_blocks_missing_traceability():
    observation = MacroObservation.from_mapping(
        {
            "market_regime": "TREND_EXPANSION",
            "macro_theme": "GOLD_MACRO_SUPPORT",
            "direction": "BUY",
            "sample_count": 5,
            "dxy_alignment_score": 75,
            "yield_alignment_score": 71,
            "inflation_surprise_score": 65,
            "labor_market_pressure": 21,
            "policy_rate_bias_score": 69,
            "news_risk_score": 23,
            "macro_consensus_score": 77,
            "execution_cost_score": 19,
        }
    )

    assert observation.is_usable is False


def test_macro_repository_groups_by_market_regime_before_theme():
    repository = MacroRepository(
        _ready_observations()
        + [
            {
                "market_regime": "range compression",
                "macro_theme": "gold macro pressure",
                "direction": "sell",
                "sample_count": 25,
                "dxy_alignment_score": 62,
                "yield_alignment_score": 66,
                "inflation_surprise_score": 58,
                "labor_market_pressure": 26,
                "policy_rate_bias_score": 63,
                "news_risk_score": 30,
                "macro_consensus_score": 65,
                "execution_cost_score": 22,
                "trace_id": "mc-003",
            }
        ]
    )

    keys = [profile.profile_key for profile in repository.build_profiles()]
    assert keys == ["RANGE_COMPRESSION:GOLD_MACRO_PRESSURE:SELL", "TREND_EXPANSION:GOLD_MACRO_SUPPORT:BUY"]


def test_macro_profile_uses_data_derived_metrics():
    profile = MacroRepository(_ready_observations()).build_profiles()[0]

    assert profile.sample_count == 26
    assert profile.average_dxy_alignment_score == 75.0
    assert profile.average_yield_alignment_score == 71.0
    assert profile.average_news_risk_score == 23.0
    assert profile.average_execution_cost_score == 19.0
    assert profile.macro_context_score == 73.56


def test_macro_profile_requires_sufficient_samples():
    profile = MacroProfile.from_observations(
        (
            MacroObservation.from_mapping(
                {
                    **_ready_observations()[0],
                    "sample_count": 2,
                }
            ),
        )
    )

    assert profile.is_ready is False


def test_macro_profile_blocks_high_news_risk():
    profile = MacroRepository(
        [{**item, "news_risk_score": 72, "news_risk": 72} for item in _ready_observations()]
    ).build_profiles()[0]

    assert profile.is_ready is False


def test_macro_policy_waits_for_empty_profiles():
    decision = MacroPolicy().decide(())

    assert decision.status == "MACRO_CONTEXT_WAIT"
    assert decision.action == "WAIT"


def test_macro_policy_selects_strongest_ready_profile():
    profiles = MacroRepository(
        _ready_observations()
        + [
            {
                "market_regime": "trend expansion",
                "macro_theme": "policy supportive gold",
                "direction": "buy",
                "sample_count": 30,
                "dxy_alignment_score": 82,
                "yield_alignment_score": 80,
                "inflation_surprise_score": 72,
                "labor_market_pressure": 16,
                "policy_rate_bias_score": 78,
                "news_risk_score": 18,
                "macro_consensus_score": 84,
                "execution_cost_score": 15,
                "trace_id": "mc-004",
            }
        ]
    ).build_profiles()

    decision = MacroPolicy().decide(profiles)

    assert decision.status == "MACRO_CONTEXT_READY"
    assert decision.selected_profile_key == "TREND_EXPANSION:POLICY_SUPPORTIVE_GOLD:BUY"


def test_macro_runtime_builds_ready_report():
    report = MacroRuntime().run(_ready_observations())

    assert report.status == "MACRO_CONTEXT_READY"
    assert report.action == "APPLY_MACRO_CONTEXT"
    assert report.active_market_regime == "TREND_EXPANSION"
    assert report.selected_macro_theme == "GOLD_MACRO_SUPPORT"
    assert report.is_ready is True


def test_macro_runtime_handles_empty_observations():
    report = MacroRuntime().run([])

    assert report.status == "MACRO_CONTEXT_WAIT"
    assert report.profile_count == 0
    assert report.is_ready is False


def test_production_milestone_e_macro_context_runtime_is_deterministic():
    runtime = ProductionMilestoneEMacroContextRuntime()

    first = runtime.run(_ready_observations())
    second = runtime.run(list(reversed(_ready_observations())))

    assert first == second
