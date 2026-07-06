"""Runtime facade for historical market database observation and summaries."""

from __future__ import annotations

from dataclasses import dataclass, field

from afip.market_history.historical_market_aggregation import HistoricalMarketAggregator
from afip.market_history.historical_market_database import HistoricalMarketDatabase
from afip.market_history.historical_market_observation import HistoricalMarketObservation
from afip.market_history.market_signature_history import MarketSignatureHistoryRepository


@dataclass
class HistoricalMarketRuntimeState:
    """Runtime state produced after processing historical market observations."""

    status: str
    database_summary: dict[str, object]
    aggregation_summary: dict[str, object]
    signature_summary: dict[str, object]
    important_observations: list[dict[str, object]] = field(default_factory=list)
    reason: str = "historical_market_runtime_ready"

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "database_summary": self.database_summary,
            "aggregation_summary": self.aggregation_summary,
            "signature_summary": self.signature_summary,
            "important_observations": list(self.important_observations),
            "reason": self.reason,
        }


class HistoricalMarketRuntime:
    """Coordinate compact history storage, period aggregation, and signature history."""

    def __init__(
        self,
        database: HistoricalMarketDatabase | None = None,
        aggregator: HistoricalMarketAggregator | None = None,
        signature_history: MarketSignatureHistoryRepository | None = None,
    ) -> None:
        self.database = database or HistoricalMarketDatabase()
        self.aggregator = aggregator or HistoricalMarketAggregator()
        self.signature_history = signature_history or MarketSignatureHistoryRepository()

    def observe(self, observation: HistoricalMarketObservation) -> HistoricalMarketRuntimeState:
        self.database.observe(observation)
        self.aggregator.observe(observation)
        self.signature_history.observe(observation)
        return self.state()

    def observe_many(self, observations: list[HistoricalMarketObservation]) -> HistoricalMarketRuntimeState:
        for observation in observations:
            self.observe(observation)
        return self.state()

    def state(self) -> HistoricalMarketRuntimeState:
        return HistoricalMarketRuntimeState(
            status="HISTORICAL_MARKET_RUNTIME_READY",
            database_summary=self.database.summary(),
            aggregation_summary=self.aggregator.summary(),
            signature_summary=self.signature_history.summary(),
            important_observations=[item.as_dict() for item in self.database.important_observations(limit=5)],
        )
