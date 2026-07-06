"""Runtime adapter for Production Milestone C Pack 15."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.learning import LearningFoundationRuntime, LearningObservation


def sample_learning_observations() -> list[LearningObservation]:
    base_time = datetime(2026, 1, 6, 8, 0, tzinfo=timezone.utc)
    results = [18.0, 14.0, 11.0, 9.0, -4.0, 16.0]
    observations: list[LearningObservation] = []
    for index, result in enumerate(results):
        observations.append(
            LearningObservation(
                observed_at=base_time + timedelta(hours=index),
                market_regime="trend",
                volatility_bucket="normal",
                direction="buy",
                signal_family="pullback continuation",
                confidence=72.0 + index,
                result_amount=result,
                execution_cost_points=3.0,
                capital_risk_amount=30.0,
                source="research_platform",
            )
        )
    observations.append(
        LearningObservation(
            observed_at=base_time + timedelta(hours=8),
            market_regime="range",
            volatility_bucket="normal",
            direction="sell",
            signal_family="mean reversion",
            confidence=61.0,
            result_amount=-6.0,
            execution_cost_points=4.0,
            capital_risk_amount=30.0,
            source="research_platform",
        )
    )
    return observations


def run_dict() -> dict[str, object]:
    return LearningFoundationRuntime().run(sample_learning_observations()).as_dict()


if __name__ == "__main__":
    import json

    print(json.dumps(run_dict(), indent=2, sort_keys=True))
