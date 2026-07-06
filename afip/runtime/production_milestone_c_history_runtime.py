"""Production Milestone C Pack 10 historical market database runtime."""

from __future__ import annotations

from datetime import datetime, timezone

from afip.market_history.historical_market_observation import HistoricalMarketObservation
from afip.market_history.historical_market_runtime import HistoricalMarketRuntime, HistoricalMarketRuntimeState


def build_default_historical_observations(now: datetime | None = None) -> list[HistoricalMarketObservation]:
    """Build deterministic seed observations for production history wiring tests."""

    timestamp = now or datetime(2026, 1, 6, 9, 0, tzinfo=timezone.utc)
    return [
        HistoricalMarketObservation(
            observed_at=timestamp,
            symbol="GOLD#",
            timeframe="H1",
            session="London",
            market_regime="Trend",
            direction="SELL",
            confidence=82.0,
            close_price=2350.25,
            spread_points=28.0,
            volatility_points=410.0,
            macro_bias="PRESSURE",
            institutional_bias="PRESSURE",
            signature_id="SIG-TREND-PRESSURE",
            stage="ENTRY",
            source="PRODUCTION_RUNTIME",
        ),
        HistoricalMarketObservation(
            observed_at=timestamp.replace(hour=10),
            symbol="GOLD#",
            timeframe="H1",
            session="London",
            market_regime="Trend",
            direction="SELL",
            confidence=78.0,
            close_price=2348.9,
            spread_points=29.0,
            volatility_points=420.0,
            macro_bias="PRESSURE",
            institutional_bias="PRESSURE",
            signature_id="SIG-TREND-PRESSURE",
            stage="REVIEW",
            source="PRODUCTION_RUNTIME",
        ),
        HistoricalMarketObservation(
            observed_at=timestamp.replace(hour=14),
            symbol="GOLD#",
            timeframe="H1",
            session="NewYork",
            market_regime="Volatile",
            direction="NEUTRAL",
            confidence=55.0,
            close_price=2353.1,
            spread_points=33.0,
            volatility_points=620.0,
            macro_bias="MIXED",
            institutional_bias="NEUTRAL",
            signature_id="SIG-VOLATILE-MIXED",
            stage="NEWS",
            source="PRODUCTION_RUNTIME",
        ),
    ]


def run_production_milestone_c_history_runtime(
    observations: list[HistoricalMarketObservation] | None = None,
) -> HistoricalMarketRuntimeState:
    """Run Pack 10 historical market database foundation."""

    runtime = HistoricalMarketRuntime()
    return runtime.observe_many(observations or build_default_historical_observations())


def run_dict(observations: list[HistoricalMarketObservation] | None = None) -> dict[str, object]:
    """Return dictionary output for scripts, dashboards, and tests."""

    return run_production_milestone_c_history_runtime(observations).as_dict()
