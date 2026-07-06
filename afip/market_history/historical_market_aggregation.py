"""Daily and session aggregation for historical market observations."""

from __future__ import annotations

from dataclasses import dataclass, field

from afip.market_history.historical_market_observation import HistoricalMarketObservation


@dataclass
class AggregatedMarketPeriod:
    """Aggregated statistics for one day or trading session."""

    period_key: str
    observation_count: int = 0
    direction_counts: dict[str, int] = field(default_factory=dict)
    regime_counts: dict[str, int] = field(default_factory=dict)
    average_confidence_total: float = 0.0
    average_spread_total: float = 0.0
    average_volatility_total: float = 0.0

    def observe(self, observation: HistoricalMarketObservation) -> None:
        self.observation_count += 1
        self.direction_counts[observation.direction] = self.direction_counts.get(observation.direction, 0) + 1
        self.regime_counts[observation.market_regime] = self.regime_counts.get(observation.market_regime, 0) + 1
        self.average_confidence_total += float(observation.confidence)
        self.average_spread_total += float(observation.spread_points)
        self.average_volatility_total += float(observation.volatility_points)

    def dominant_direction(self) -> str:
        return self._dominant(self.direction_counts)

    def dominant_regime(self) -> str:
        return self._dominant(self.regime_counts)

    @staticmethod
    def _dominant(values: dict[str, int]) -> str:
        if not values:
            return "NEUTRAL"
        return sorted(values.items(), key=lambda item: (-item[1], item[0]))[0][0]

    def as_dict(self) -> dict[str, object]:
        divisor = self.observation_count or 1
        return {
            "period_key": self.period_key,
            "observation_count": self.observation_count,
            "dominant_direction": self.dominant_direction(),
            "dominant_regime": self.dominant_regime(),
            "direction_counts": dict(sorted(self.direction_counts.items())),
            "regime_counts": dict(sorted(self.regime_counts.items())),
            "average_confidence": round(self.average_confidence_total / divisor, 4),
            "average_spread": round(self.average_spread_total / divisor, 4),
            "average_volatility": round(self.average_volatility_total / divisor, 4),
        }


class HistoricalMarketAggregator:
    """Aggregate observations into daily and session-level summaries."""

    def __init__(self) -> None:
        self._daily: dict[str, AggregatedMarketPeriod] = {}
        self._session: dict[str, AggregatedMarketPeriod] = {}

    def observe(self, observation: HistoricalMarketObservation) -> dict[str, AggregatedMarketPeriod]:
        day = self._daily.setdefault(observation.day_key, AggregatedMarketPeriod(period_key=observation.day_key))
        session = self._session.setdefault(observation.session_key, AggregatedMarketPeriod(period_key=observation.session_key))
        day.observe(observation)
        session.observe(observation)
        return {"daily": day, "session": session}

    def daily_summary(self) -> list[dict[str, object]]:
        return [period.as_dict() for key, period in sorted(self._daily.items())]

    def session_summary(self) -> list[dict[str, object]]:
        return [period.as_dict() for key, period in sorted(self._session.items())]

    def summary(self) -> dict[str, object]:
        return {
            "status": "HISTORICAL_MARKET_AGGREGATION_READY",
            "daily_periods": len(self._daily),
            "session_periods": len(self._session),
            "daily": self.daily_summary(),
            "session": self.session_summary(),
        }
