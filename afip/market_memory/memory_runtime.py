"""Production Milestone E Pack 3 market memory runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .memory_policy import MarketMemoryPolicy
from .memory_report import MarketMemoryReport
from .memory_repository import MarketMemoryRepository


class MarketMemoryRuntime:
    """Build deterministic market memory from regime-first historical observations."""

    def __init__(self, policy: MarketMemoryPolicy | None = None) -> None:
        self.policy = policy or MarketMemoryPolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> MarketMemoryReport:
        repository = MarketMemoryRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(profiles)
        return MarketMemoryReport.from_profiles(profiles, decision)
