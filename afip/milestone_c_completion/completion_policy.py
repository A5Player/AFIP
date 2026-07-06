"""Final completion policy for Production Milestone C."""

from __future__ import annotations

from dataclasses import dataclass

from .completion_registry import MilestoneCompletionRegistry


@dataclass(frozen=True)
class MilestoneCompletionDecision:
    status: str
    readiness: str
    completion_ratio: float
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "readiness": self.readiness,
            "completion_ratio": self.completion_ratio,
            "reasons": list(self.reasons),
        }


class MilestoneCompletionPolicy:
    def decide(self, registry: MilestoneCompletionRegistry) -> MilestoneCompletionDecision:
        if registry.missing_pack_ids:
            return MilestoneCompletionDecision(
                "MILESTONE_C_INCOMPLETE",
                "WAIT",
                registry.completion_ratio,
                ("required_milestone_c_pack_missing",),
            )
        if registry.failed_capability_keys:
            return MilestoneCompletionDecision(
                "MILESTONE_C_QUALITY_BLOCKED",
                "BLOCKED",
                registry.completion_ratio,
                ("milestone_c_quality_evidence_not_passed",),
            )
        if not registry.dependency_sequence_ready:
            return MilestoneCompletionDecision(
                "MILESTONE_C_SEQUENCE_REVIEW",
                "WAIT",
                registry.completion_ratio,
                ("milestone_c_dependency_sequence_required",),
            )
        return MilestoneCompletionDecision(
            "MILESTONE_C_COMPLETE",
            "READY",
            registry.completion_ratio,
            ("milestone_c_completion_confirmed",),
        )
