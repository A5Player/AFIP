"""Production Milestone E Pack 9 adaptive learning runtime wrapper."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.adaptive_learning import AdaptiveLearningReport, AdaptiveLearningRuntime


class ProductionMilestoneEAdaptiveLearningRuntime:
    """Production wrapper for deterministic adaptive learning intelligence."""

    def __init__(self) -> None:
        self.runtime = AdaptiveLearningRuntime()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> AdaptiveLearningReport:
        return self.runtime.run(observations)
