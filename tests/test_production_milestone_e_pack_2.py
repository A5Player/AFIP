from afip.runtime.production_milestone_e_volatility_intelligence_runtime import (
    run_production_milestone_e_volatility_intelligence,
)
from afip.volatility_intelligence import (
    VolatilityIntelligencePolicy,
    VolatilityObservation,
    VolatilityRepository,
)


def _sample(state="EXPANSION", regime="TRENDING", samples=12, outcome=68.0, cost=72.0, expansion=74.0, compression=22.0, trace="v1"):
    return {
        "market_regime": regime,
        "volatility_state": state,
        "direction": "BUY",
        "sample_count": samples,
        "atr_points": 88.0,
        "realized_volatility": 66.0,
        "expected_volatility": 64.0,
        "expansion_score": expansion,
        "compression_score": compression,
        "execution_cost_score": cost,
        "favorable_outcome_rate": outcome,
        "trace_id": trace,
    }


def _ready_observations():
    return [
        _sample(state="Expansion", samples=12, trace="e1"),
        _sample(state="Expansion", samples=11, trace="e2"),
        _sample(state="Compression", samples=14, outcome=72.0, cost=76.0, expansion=25.0, compression=82.0, trace="c1"),
        _sample(state="Compression", samples=12, outcome=70.0, cost=78.0, expansion=20.0, compression=80.0, trace="c2"),
    ]


def test_volatility_observation_normalizes_market_regime_first_key():
    observation = VolatilityObservation.from_mapping(_sample(state="range-expansion", regime="trend continuation"))
    assert observation.market_regime == "TREND_CONTINUATION"
    assert observation.volatility_state == "RANGE_EXPANSION"
    assert observation.regime_volatility_key.startswith("TREND_CONTINUATION:RANGE_EXPANSION")


def test_volatility_observation_blocks_missing_traceability():
    observation = VolatilityObservation.from_mapping(_sample(trace=""))
    assert observation.is_usable is False


def test_volatility_repository_groups_by_market_regime_before_state():
    repository = VolatilityRepository(_ready_observations())
    profile_keys = tuple(profile.profile_key for profile in repository.build_profiles())
    assert profile_keys == ("TRENDING:COMPRESSION:BUY", "TRENDING:EXPANSION:BUY")


def test_volatility_profile_uses_data_derived_metrics():
    profile = VolatilityRepository(_ready_observations()).build_profiles()[1]
    assert profile.sample_count == 23
    assert profile.average_realized_volatility == 66.0
    assert profile.volatility_edge_score > 60.0


def test_volatility_profile_requires_sufficient_samples():
    profile = VolatilityRepository([_sample(samples=5, trace="small")]).build_profiles()[0]
    assert profile.is_ready is False


def test_volatility_profile_blocks_low_execution_cost_quality():
    profile = VolatilityRepository([
        _sample(samples=12, cost=42.0, trace="c1"),
        _sample(samples=12, cost=45.0, trace="c2"),
    ]).build_profiles()[0]
    assert profile.is_ready is False


def test_volatility_policy_waits_for_empty_profiles():
    decision = VolatilityIntelligencePolicy().decide(())
    assert decision.status == "VOLATILITY_INTELLIGENCE_WAIT"
    assert decision.action == "WAIT"


def test_volatility_policy_selects_strongest_ready_profile():
    profiles = VolatilityRepository(_ready_observations()).build_profiles()
    decision = VolatilityIntelligencePolicy().decide(profiles)
    assert decision.status == "VOLATILITY_INTELLIGENCE_READY"
    assert decision.selected_profile_key == "TRENDING:COMPRESSION:BUY"


def test_volatility_runtime_builds_ready_report():
    report = run_production_milestone_e_volatility_intelligence(_ready_observations())
    assert report.status == "VOLATILITY_INTELLIGENCE_READY"
    assert report.selected_volatility_state == "COMPRESSION"
    assert report.is_ready is True


def test_volatility_runtime_handles_empty_observations():
    report = run_production_milestone_e_volatility_intelligence([])
    assert report.status == "VOLATILITY_INTELLIGENCE_WAIT"
    assert report.is_ready is False


def test_production_milestone_e_volatility_intelligence_runtime_is_deterministic():
    first = run_production_milestone_e_volatility_intelligence(_ready_observations())
    second = run_production_milestone_e_volatility_intelligence(_ready_observations())
    assert first == second
