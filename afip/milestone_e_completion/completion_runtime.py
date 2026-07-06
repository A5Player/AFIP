"""Runtime for Production Milestone E Pack 10 final completion."""

from __future__ import annotations

from typing import Any, Mapping

from .completion_evidence import MilestoneECapabilityEvidence
from .completion_policy import MilestoneECompletionPolicy
from .completion_registry import MilestoneECompletionRegistry
from .completion_report import MilestoneECompletionReport, MilestoneECompletionReporter


class MilestoneECompletionRuntime:
    def __init__(self) -> None:
        self.policy = MilestoneECompletionPolicy()
        self.reporter = MilestoneECompletionReporter()

    def run(self, values: list[MilestoneECapabilityEvidence | Mapping[str, Any]]) -> MilestoneECompletionReport:
        evidence = [value if isinstance(value, MilestoneECapabilityEvidence) else MilestoneECapabilityEvidence.from_mapping(value) for value in values]
        registry = MilestoneECompletionRegistry.build(evidence)
        decision = self.policy.decide(registry)
        return self.reporter.build(registry, decision)
