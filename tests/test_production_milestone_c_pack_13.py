from __future__ import annotations

from datetime import datetime, timezone

from afip.parameters.adaptive_parameter_runtime import AdaptiveParameterRuntime
from afip.parameters.parameter_observation import ParameterObservation
from afip.parameters.parameter_quality import ParameterQualityAssessment
from afip.parameters.parameter_repository import ParameterRepository
from afip.runtime.production_milestone_c_adaptive_parameter_runtime import run_dict, sample_observations


def _observation(result: float = 10.0, *, cost: float = 24.0, regime: str = "trend") -> ParameterObservation:
    return ParameterObservation(
        observed_at=datetime(2026, 1, 6, 8, 0, tzinfo=timezone.utc),
        symbol="gold#",
        position_direction="buy",
        market_regime=regime,
        volatility_bucket="normal",
        entry_quality=82.0,
        result_amount=result,
        stop_distance_points=180.0,
        favorable_excursion_points=260.0,
        adverse_excursion_points=100.0,
        holding_minutes=45.0,
        execution_cost_points=cost,
    )


def test_parameter_observation_normalizes_regime_first_key() -> None:
    observation = _observation()
    assert observation.symbol == "GOLD#"
    assert observation.market_regime == "TREND"
    assert observation.parameter_key == "GOLD#|TREND|NORMAL|BUY"


def test_parameter_repository_groups_by_market_regime_and_direction() -> None:
    repository = ParameterRepository()
    repository.observe(_observation(12.0))
    repository.observe(_observation(14.0, regime="expansion"))
    data = repository.as_dict()
    assert data["unique_profiles"] == 2
    assert data["total_observations"] == 2


def test_parameter_profile_builds_adaptive_candidate_without_hardcoded_signal_values() -> None:
    repository = ParameterRepository()
    for result in [20.0, 18.0, 16.0, -4.0, 22.0]:
        repository.observe(_observation(result))
    candidate = repository.ranked()[0].candidate()
    assert candidate["adaptive_stop_points"] >= 100.0
    assert candidate["profit_objective_points"] > candidate["adaptive_stop_points"]
    assert 55.0 <= candidate["confidence_floor"] <= 86.0


def test_parameter_quality_requires_sufficient_profitable_low_cost_profile() -> None:
    repository = ParameterRepository()
    for result in [20.0, 18.0, 16.0, -4.0, 22.0]:
        profile = repository.observe(_observation(result))
    result = ParameterQualityAssessment(minimum_observations=5).assess(profile)
    assert result.status == "PARAMETER_RESEARCH_READY"
    assert result.approved is True


def test_parameter_quality_blocks_high_execution_cost() -> None:
    repository = ParameterRepository()
    for result in [20.0, 18.0, 16.0, 12.0, 22.0]:
        profile = repository.observe(_observation(result, cost=70.0))
    result = ParameterQualityAssessment(maximum_average_cost_points=45.0).assess(profile)
    assert result.status == "PARAMETER_OBSERVE_ONLY"
    assert "execution_cost_above_parameter_threshold" in result.reasons


def test_adaptive_parameter_runtime_handles_empty_observations() -> None:
    state = AdaptiveParameterRuntime().run([])
    assert state.status == "ADAPTIVE_PARAMETER_REVIEW"
    assert state.reason == "no_parameter_observations"


def test_adaptive_parameter_runtime_builds_ready_state() -> None:
    state = AdaptiveParameterRuntime(quality=ParameterQualityAssessment(minimum_observations=5)).run(sample_observations())
    assert state.status == "ADAPTIVE_PARAMETER_READY"
    assert state.selected_profile is not None
    assert state.selected_profile["candidate"]["profit_objective_points"] > 0.0


def test_production_milestone_c_adaptive_parameter_runtime_is_deterministic() -> None:
    first = run_dict()
    second = run_dict()
    assert first == second
    assert first["status"] == "ADAPTIVE_PARAMETER_READY"
