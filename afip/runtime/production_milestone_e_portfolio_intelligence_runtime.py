"""Production Milestone E Pack 7 portfolio intelligence runtime facade."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.portfolio_intelligence import PortfolioReport, PortfolioRuntime


class ProductionMilestoneEPortfolioIntelligenceRuntime:
    """Stable facade used by Pack 7 tests and future production integration."""

    def __init__(self) -> None:
        self.runtime = PortfolioRuntime()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> PortfolioReport:
        normalized = tuple(observations)
        return self.runtime.run(normalized)
