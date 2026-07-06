"""Production entrypoint for Milestone C Pack 16 market regime intelligence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.regime import MarketRegimeRuntime, RegimeEvidence


def sample_regime_evidence() -> list[RegimeEvidence]:
    base = datetime(2026, 1, 7, 8, 0, tzinfo=timezone.utc)
    values = [
        ("quiet", "low", "flat", 0.18, 24.0, 44.0, 4.0, 1.0),
        ("normal", "normal", "buy", 0.42, 52.0, 61.0, 8.0, 6.0),
        ("normal", "normal", "sell", 0.55, 58.0, 64.0, 7.0, 7.0),
        ("expansion", "high", "buy", 0.96, 76.0, 82.0, 12.0, 14.0),
        ("expansion", "high", "buy", 1.12, 79.0, 86.0, 11.0, 16.0),
        ("expansion", "high", "sell", 1.28, 73.0, 79.0, 15.0, 11.0),
        ("quiet", "low", "flat", 0.24, 28.0, 47.0, 5.0, 2.0),
    ]
    return [
        RegimeEvidence(
            observed_at=base + timedelta(hours=index),
            market_regime=regime,
            volatility_bucket=volatility,
            direction=direction,
            range_percent=range_percent,
            trend_efficiency=efficiency,
            participation_score=participation,
            transition_pressure=pressure,
            result_amount=result,
        )
        for index, (regime, volatility, direction, range_percent, efficiency, participation, pressure, result) in enumerate(values)
    ]


def sample_current_snapshot() -> dict[str, float]:
    return {
        "range_percent": 1.05,
        "trend_efficiency": 78.0,
        "participation_score": 84.0,
        "transition_pressure": 10.0,
        "directional_pressure": 1.0,
    }


def run_dict() -> dict[str, object]:
    return MarketRegimeRuntime().run(sample_regime_evidence(), sample_current_snapshot()).as_dict()
