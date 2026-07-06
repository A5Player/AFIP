"""Production Milestone C Pack 13 adaptive parameter runtime entrypoint."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.parameters.adaptive_parameter_runtime import AdaptiveParameterRuntime
from afip.parameters.parameter_observation import ParameterObservation
from afip.parameters.parameter_quality import ParameterQualityAssessment


def sample_observations() -> list[ParameterObservation]:
    base = datetime(2026, 1, 6, 8, 0, tzinfo=timezone.utc)
    observations: list[ParameterObservation] = []
    results = [20.0, 18.0, 14.0, -4.0, 16.0, 24.0]
    for index, result in enumerate(results):
        observations.append(
            ParameterObservation(
                observed_at=base + timedelta(hours=index),
                symbol="GOLD#",
                position_direction="BUY",
                market_regime="TREND",
                volatility_bucket="NORMAL",
                session="LONDON",
                entry_quality=82.0,
                result_amount=result,
                stop_distance_points=180.0,
                favorable_excursion_points=260.0 + index * 5.0,
                adverse_excursion_points=90.0 + index * 4.0,
                holding_minutes=40.0 + index,
                execution_cost_points=24.0,
                tags=("PULLBACK", "REGIME_ALIGNED"),
            )
        )
    observations.append(
        ParameterObservation(
            observed_at=base + timedelta(hours=8),
            symbol="GOLD#",
            position_direction="SELL",
            market_regime="EXPANSION",
            volatility_bucket="HIGH",
            session="NEW_YORK",
            entry_quality=70.0,
            result_amount=-10.0,
            stop_distance_points=230.0,
            favorable_excursion_points=130.0,
            adverse_excursion_points=190.0,
            holding_minutes=18.0,
            execution_cost_points=34.0,
            tags=("COST_REVIEW",),
        )
    )
    return observations


def run() -> object:
    return AdaptiveParameterRuntime(quality=ParameterQualityAssessment(minimum_observations=5)).run(sample_observations())


def run_dict() -> dict[str, object]:
    return run().as_dict()
