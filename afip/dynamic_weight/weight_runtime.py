"""Production Milestone E Pack 5 dynamic weight runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .weight_policy import DynamicWeightPolicy
from .weight_report import DynamicWeightReport
from .weight_repository import DynamicWeightRepository


class DynamicWeightRuntime:
    """Build deterministic intelligence weights from regime-first observations."""

    def __init__(self, policy: DynamicWeightPolicy | None = None) -> None:
        self.policy = policy or DynamicWeightPolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> DynamicWeightReport:
        repository = DynamicWeightRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(profiles)
        return DynamicWeightReport.from_profiles(profiles, decision)
