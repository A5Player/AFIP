"""Production Milestone E Pack 8 macro context runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .macro_policy import MacroPolicy
from .macro_report import MacroReport
from .macro_repository import MacroRepository


class MacroRuntime:
    """Build deterministic macro context from regime-first observations."""

    def __init__(self, policy: MacroPolicy | None = None) -> None:
        self.policy = policy or MacroPolicy()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> MacroReport:
        repository = MacroRepository(observations)
        profiles = repository.build_profiles()
        decision = self.policy.decide(profiles)
        return MacroReport.from_profiles(profiles, decision)
