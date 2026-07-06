"""Runtime for Production Milestone C Pack 20 final completion."""

from __future__ import annotations

from typing import Any, Mapping

from .completion_evidence import MilestoneCapabilityEvidence
from .completion_policy import MilestoneCompletionPolicy
from .completion_registry import MilestoneCompletionRegistry
from .completion_report import MilestoneCompletionReport, MilestoneCompletionReporter


class MilestoneCompletionRuntime:
    def __init__(self) -> None:
        self.policy = MilestoneCompletionPolicy()
        self.reporter = MilestoneCompletionReporter()

    def run(self, values: list[MilestoneCapabilityEvidence | Mapping[str, Any]]) -> MilestoneCompletionReport:
        evidence = [value if isinstance(value, MilestoneCapabilityEvidence) else MilestoneCapabilityEvidence.from_mapping(value) for value in values]
        registry = MilestoneCompletionRegistry.build(evidence)
        decision = self.policy.decide(registry)
        return self.reporter.build(registry, decision)
