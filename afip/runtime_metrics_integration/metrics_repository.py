"""In-memory runtime metrics repository for deterministic review workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from .metrics_profile import RuntimeMetricsProfile


@dataclass
class RuntimeMetricsRepository:
    """Simple append-only repository contract for runtime metrics profiles."""

    _profiles: List[RuntimeMetricsProfile] = field(default_factory=list)

    def append(self, profile: RuntimeMetricsProfile) -> None:
        self._profiles.append(profile)

    def extend(self, profiles: Iterable[RuntimeMetricsProfile]) -> None:
        for profile in profiles:
            self.append(profile)

    def all(self) -> list[RuntimeMetricsProfile]:
        return list(self._profiles)

    def latest(self) -> RuntimeMetricsProfile | None:
        if not self._profiles:
            return None
        return self._profiles[-1]
