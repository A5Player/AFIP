from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.learning import LearningFoundationRuntime, LearningGovernor, LearningObservation, LearningProfileRepository
from afip.runtime.production_milestone_c_learning_foundation_runtime import run_dict, sample_learning_observations


def _observation(result: float = 12.0, *, cost: float = 3.0, regime: str = "trend", direction: str = "buy") -> LearningObservation:
    return LearningObservation(
        observed_at=datetime(2026, 1, 6, 8, 0, tzinfo=timezone.utc),
        market_regime=regime,
        volatility_bucket="normal",
        direction=direction,
        signal_family="pullback continuation",
        confidence=74.0,
        result_amount=result,
        execution_cost_points=cost,
        capital_risk_amount=30.0,
    )


def test_learning_observation_normalizes_regime_first_key() -> None:
    observation = _observation(direction="buy")
    assert observation.direction == "BUY"
    assert observation.regime_first_key.startswith("TREND|NORMAL|BUY")
    assert observation.net_learning_amount == 9.0


def test_learning_repository_groups_by_market_regime_before_signal_family() -> None:
    repository = LearningProfileRepository()
    repository.add(_observation(12.0, regime="trend"))
    repository.add(_observation(8.0, regime="range"))
    keys = list(repository.grouped().keys())
    assert keys[0].startswith("RANGE|")
    assert keys[1].startswith("TREND|")


def test_learning_repository_profiles_use_data_derived_metrics() -> None:
    repository = LearningProfileRepository([_observation(12.0), _observation(-4.0)])
    profile = repository.profiles()[0]
    assert profile.observations == 2
    assert profile.win_rate == 50.0
    assert profile.expectancy == 1.0
    assert profile.average_execution_cost_points == 3.0


def test_learning_governor_observe_only_for_small_samples() -> None:
    profile = LearningProfileRepository([_observation(12.0)]).profiles()[0].as_dict()
    result = LearningGovernor(minimum_observations=3).evaluate(profile)
    assert result.status == "LEARNING_OBSERVE_ONLY"
    assert "insufficient_learning_observations" in result.reasons


def test_learning_governor_update_ready_for_profitable_low_cost_profile() -> None:
    repository = LearningProfileRepository(_observation(12.0 + index) for index in range(5))
    result = LearningGovernor(minimum_observations=5).evaluate(repository.profiles()[0].as_dict())
    assert result.status == "LEARNING_UPDATE_READY"
    assert result.action == "PROPOSE_BOUNDED_PARAMETER_UPDATE"


def test_learning_governor_blocks_high_execution_cost() -> None:
    records = []
    for index in range(5):
        records.append(
            LearningObservation(
                observed_at=datetime(2026, 1, 6, 8, 0, tzinfo=timezone.utc) + timedelta(hours=index),
                market_regime="trend",
                volatility_bucket="normal",
                direction="buy",
                signal_family="pullback continuation",
                confidence=75.0,
                result_amount=80.0,
                execution_cost_points=60.0,
                capital_risk_amount=30.0,
            )
        )
    profile = LearningProfileRepository(records).profiles()[0].as_dict()
    result = LearningGovernor(maximum_average_cost_points=45.0).evaluate(profile)
    assert result.status == "LEARNING_OBSERVE_ONLY"
    assert "learning_execution_cost_above_threshold" in result.reasons


def test_learning_foundation_runtime_builds_ready_state() -> None:
    state = LearningFoundationRuntime().run(sample_learning_observations())
    assert state.status == "LEARNING_FOUNDATION_READY"
    assert state.repository["observation_count"] == 7
    assert state.best_result is not None
    assert state.best_result["status"] == "LEARNING_UPDATE_READY"


def test_learning_foundation_runtime_handles_empty_observations() -> None:
    state = LearningFoundationRuntime().run([])
    assert state.status == "LEARNING_DATA_REQUIRED"
    assert state.reason == "no_learning_observations"


def test_production_milestone_c_learning_foundation_runtime_is_deterministic() -> None:
    first = run_dict()
    second = run_dict()
    assert first == second
    assert first["status"] == "LEARNING_FOUNDATION_READY"
