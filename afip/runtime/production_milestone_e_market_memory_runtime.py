"""Production Milestone E Pack 3 market memory runtime facade."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.market_memory import MarketMemoryReport, MarketMemoryRuntime


class ProductionMilestoneEMarketMemoryRuntime:
    """Production facade for deterministic market memory intelligence."""

    def __init__(self, runtime: MarketMemoryRuntime | None = None) -> None:
        self.runtime = runtime or MarketMemoryRuntime()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> MarketMemoryReport:
        return self.runtime.run(observations)
