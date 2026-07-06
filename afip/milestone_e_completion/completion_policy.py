"""Final completion policy for Production Milestone E."""

from __future__ import annotations

from dataclasses import dataclass

from .completion_registry import MilestoneECompletionRegistry


@dataclass(frozen=True)
class MilestoneECompletionDecision:
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


class MilestoneECompletionPolicy:
    def decide(self, registry: MilestoneECompletionRegistry) -> MilestoneECompletionDecision:
        if registry.missing_pack_ids:
            return MilestoneECompletionDecision(
                "MILESTONE_E_INCOMPLETE",
                "WAIT",
                registry.completion_ratio,
                ("required_milestone_e_pack_missing",),
            )
        if registry.failed_capability_keys:
            return MilestoneECompletionDecision(
                "MILESTONE_E_QUALITY_BLOCKED",
                "BLOCKED",
                registry.completion_ratio,
                ("milestone_e_quality_evidence_not_passed",),
            )
        if not registry.intelligence_sequence_ready:
            return MilestoneECompletionDecision(
                "MILESTONE_E_SEQUENCE_REVIEW",
                "WAIT",
                registry.completion_ratio,
                ("milestone_e_intelligence_sequence_required",),
            )
        if not registry.knowledge_first_ready:
            return MilestoneECompletionDecision(
                "MILESTONE_E_KNOWLEDGE_REVIEW",
                "WAIT",
                registry.completion_ratio,
                ("milestone_e_knowledge_first_evidence_required",),
            )
        return MilestoneECompletionDecision(
            "MILESTONE_E_COMPLETE",
            "READY",
            registry.completion_ratio,
            ("milestone_e_completion_confirmed",),
        )
