from afip.runtime.production_milestone_e_session_intelligence_runtime import (
    run_production_milestone_e_session_intelligence,
)
from afip.session_intelligence import (
    SessionIntelligencePolicy,
    SessionObservation,
    SessionRepository,
)


def _sample(session="LONDON", regime="TRENDING", samples=12, outcome=68.0, cost=72.0, trace="t1"):
    return {
        "market_regime": regime,
        "session_key": session,
        "overlap_key": "LONDON_NEW_YORK" if str(session).strip().upper().replace(" ", "_") == "NEW_YORK" else "NONE",
        "direction": "BUY",
        "sample_count": samples,
        "average_range_points": 72.0,
        "realized_volatility": 64.0,
        "liquidity_score": 75.0,
        "execution_cost_score": cost,
        "favorable_outcome_rate": outcome,
        "trace_id": trace,
    }


def _ready_observations():
    return [
        _sample(session="London", samples=12, trace="l1"),
        _sample(session="London", samples=11, trace="l2"),
        _sample(session="New York", samples=14, outcome=72.0, cost=76.0, trace="n1"),
        _sample(session="New York", samples=12, outcome=70.0, cost=78.0, trace="n2"),
    ]


def test_session_observation_normalizes_market_regime_first_key():
    observation = SessionObservation.from_mapping(_sample(session="new-york", regime="range expansion"))
    assert observation.market_regime == "RANGE_EXPANSION"
    assert observation.session_key == "NEW_YORK"
    assert observation.regime_session_key.startswith("RANGE_EXPANSION:NEW_YORK")


def test_session_observation_blocks_missing_traceability():
    observation = SessionObservation.from_mapping(_sample(trace=""))
    assert observation.is_usable is False


def test_session_repository_groups_by_market_regime_before_session():
    repository = SessionRepository(_ready_observations())
    profile_keys = tuple(profile.profile_key for profile in repository.build_profiles())
    assert profile_keys == ("TRENDING:LONDON:NONE:BUY", "TRENDING:NEW_YORK:LONDON_NEW_YORK:BUY")


def test_session_profile_uses_data_derived_metrics():
    profile = SessionRepository(_ready_observations()).build_profiles()[0]
    assert profile.sample_count == 23
    assert profile.average_liquidity_score == 75.0
    assert profile.session_strength_score > 60.0


def test_session_profile_requires_sufficient_samples():
    profile = SessionRepository([_sample(samples=5, trace="small")]).build_profiles()[0]
    assert profile.is_ready is False


def test_session_profile_blocks_low_execution_cost_quality():
    profile = SessionRepository([
        _sample(samples=12, cost=42.0, trace="c1"),
        _sample(samples=12, cost=45.0, trace="c2"),
    ]).build_profiles()[0]
    assert profile.is_ready is False


def test_session_policy_waits_for_empty_profiles():
    decision = SessionIntelligencePolicy().decide(())
    assert decision.status == "SESSION_INTELLIGENCE_WAIT"
    assert decision.action == "WAIT"


def test_session_policy_selects_strongest_ready_profile():
    profiles = SessionRepository(_ready_observations()).build_profiles()
    decision = SessionIntelligencePolicy().decide(profiles)
    assert decision.status == "SESSION_INTELLIGENCE_READY"
    assert decision.selected_profile_key == "TRENDING:NEW_YORK:LONDON_NEW_YORK:BUY"


def test_session_runtime_builds_ready_report():
    report = run_production_milestone_e_session_intelligence(_ready_observations())
    assert report.status == "SESSION_INTELLIGENCE_READY"
    assert report.selected_session == "NEW_YORK"
    assert report.is_ready is True


def test_session_runtime_handles_empty_observations():
    report = run_production_milestone_e_session_intelligence([])
    assert report.status == "SESSION_INTELLIGENCE_WAIT"
    assert report.is_ready is False


def test_production_milestone_e_session_intelligence_runtime_is_deterministic():
    first = run_production_milestone_e_session_intelligence(_ready_observations())
    second = run_production_milestone_e_session_intelligence(_ready_observations())
    assert first == second
