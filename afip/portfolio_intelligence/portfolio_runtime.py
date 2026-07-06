"""Production Milestone E Pack 7 portfolio intelligence runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .portfolio_policy import PortfolioPolicy
from .portfolio_report import PortfolioReport
from .portfolio_repository import PortfolioRepository


class PortfolioRuntime:
    """Build deterministic portfolio context from regime-first observations."""

    def __init__(self, policy: PortfolioPolicy | None = None) -> None:
        self.policy = policy or PortfolioPolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> PortfolioReport:
        repository = PortfolioRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(profiles)
        return PortfolioReport.from_profiles(profiles, decision)
