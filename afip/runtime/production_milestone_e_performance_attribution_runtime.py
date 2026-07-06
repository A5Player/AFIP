"""Production Milestone E Pack 6 performance attribution runtime entrypoint."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.performance_attribution import PerformanceAttributionReport, PerformanceAttributionRuntime


class ProductionMilestoneEPerformanceAttributionRuntime:
    """Production wrapper for deterministic performance attribution intelligence."""

    def __init__(self, runtime: PerformanceAttributionRuntime | None = None) -> None:
        self.runtime = runtime or PerformanceAttributionRuntime()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> PerformanceAttributionReport:
        return self.runtime.run(observations)
