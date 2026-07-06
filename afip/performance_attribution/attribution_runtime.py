"""Production Milestone E Pack 6 performance attribution runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .attribution_policy import PerformanceAttributionPolicy
from .attribution_report import PerformanceAttributionReport
from .attribution_repository import PerformanceAttributionRepository


class PerformanceAttributionRuntime:
    """Build deterministic attribution context from regime-first observations."""

    def __init__(self, policy: PerformanceAttributionPolicy | None = None) -> None:
        self.policy = policy or PerformanceAttributionPolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> PerformanceAttributionReport:
        repository = PerformanceAttributionRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(profiles)
        return PerformanceAttributionReport.from_profiles(profiles, decision)
