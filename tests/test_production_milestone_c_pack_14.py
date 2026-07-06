from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.research import ResearchDataset, ResearchHypothesis, ResearchPlatformRuntime, ResearchSample
from afip.runtime.production_milestone_c_research_platform_runtime import run_dict, sample_research_records


def _sample(result: float = 10.0, *, cost: float = 24.0, regime: str = "trend", direction: str = "buy") -> ResearchSample:
    return ResearchSample(
        observed_at=datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc),
        symbol="gold#",
        market_regime=regime,
        volatility_bucket="normal",
        direction=direction,
        signal_family="pullback continuation",
        confidence=74.0,
        result_amount=result,
        execution_cost_points=cost,
        holding_minutes=45.0,
    )


def test_research_sample_normalizes_regime_first_key() -> None:
    sample = _sample(direction="buy")
    assert sample.symbol == "GOLD#"
    assert sample.direction == "BUY"
    assert sample.regime_first_key.startswith("TREND|NORMAL|BUY")


def test_research_dataset_groups_by_market_regime_before_signal_family() -> None:
    dataset = ResearchDataset()
    dataset.add(_sample(10.0, regime="trend"))
    dataset.add(_sample(8.0, regime="range"))
    keys = list(dataset.grouped().keys())
    assert keys[0].startswith("RANGE|")
    assert keys[1].startswith("TREND|")


def test_research_dataset_summary_uses_data_derived_metrics() -> None:
    dataset = ResearchDataset()
    dataset.add(_sample(12.0))
    dataset.add(_sample(-4.0))
    summary = dataset.group_summary()[0]
    assert summary["observations"] == 2
    assert summary["win_rate"] == 50.0
    assert summary["expectancy"] == 4.0
    assert summary["average_execution_cost_points"] == 24.0


def test_research_hypothesis_observe_only_for_small_samples() -> None:
    dataset = ResearchDataset([_sample(12.0)])
    result = ResearchHypothesis(minimum_observations=3).evaluate(dataset.group_summary()[0])
    assert result.status == "RESEARCH_OBSERVE_ONLY"
    assert "insufficient_research_observations" in result.reasons


def test_research_hypothesis_review_ready_for_profitable_low_cost_group() -> None:
    dataset = ResearchDataset()
    for index in range(5):
        dataset.add(_sample(10.0 + index))
    result = ResearchHypothesis(minimum_observations=5).evaluate(dataset.group_summary()[0])
    assert result.status == "RESEARCH_REVIEW_READY"
    assert result.observations == 5


def test_research_hypothesis_blocks_high_execution_cost() -> None:
    dataset = ResearchDataset()
    for index in range(5):
        dataset.add(
            ResearchSample(
                observed_at=datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc) + timedelta(hours=index),
                market_regime="trend",
                direction="buy",
                signal_family="pullback continuation",
                confidence=75.0,
                result_amount=12.0,
                execution_cost_points=80.0,
                holding_minutes=30.0,
            )
        )
    result = ResearchHypothesis(maximum_average_cost_points=45.0).evaluate(dataset.group_summary()[0])
    assert result.status == "RESEARCH_OBSERVE_ONLY"
    assert "execution_cost_above_research_threshold" in result.reasons


def test_research_platform_runtime_builds_ready_state() -> None:
    state = ResearchPlatformRuntime().run(sample_research_records())
    assert state.status == "RESEARCH_PLATFORM_READY"
    assert state.dataset["sample_count"] == 8
    assert state.best_result is not None
    assert state.best_result["status"] == "RESEARCH_REVIEW_READY"


def test_research_platform_runtime_handles_empty_samples() -> None:
    state = ResearchPlatformRuntime().run([])
    assert state.status == "RESEARCH_DATA_REQUIRED"
    assert state.reason == "no_research_samples"


def test_production_milestone_c_research_platform_runtime_is_deterministic() -> None:
    first = run_dict()
    second = run_dict()
    assert first == second
    assert first["status"] == "RESEARCH_PLATFORM_READY"
