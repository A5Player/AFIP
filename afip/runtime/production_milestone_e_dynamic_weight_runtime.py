"""Production Milestone E Pack 5 dynamic weight runtime entrypoint."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.dynamic_weight import DynamicWeightReport, DynamicWeightRuntime


class ProductionMilestoneEDynamicWeightRuntime:
    """Production wrapper for deterministic dynamic weight intelligence."""

    def __init__(self, runtime: DynamicWeightRuntime | None = None) -> None:
        self.runtime = runtime or DynamicWeightRuntime()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> DynamicWeightReport:
        return self.runtime.run(observations)
