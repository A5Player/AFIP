"""Final report model for Production Milestone C completion."""

from __future__ import annotations

from dataclasses import dataclass

from .completion_policy import MilestoneCompletionDecision
from .completion_registry import MilestoneCompletionRegistry


@dataclass(frozen=True)
class MilestoneCompletionReport:
    status: str
    registry: dict[str, object]
    decision: dict[str, object]
    audit: dict[str, object]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "registry": dict(self.registry),
            "decision": dict(self.decision),
            "audit": dict(self.audit),
            "reason": self.reason,
        }


class MilestoneCompletionReporter:
    def build(self, registry: MilestoneCompletionRegistry, decision: MilestoneCompletionDecision) -> MilestoneCompletionReport:
        audit = {
            "adaptive_parameters_ready": 13 in registry.ordered_pack_ids,
            "research_platform_ready": 14 in registry.ordered_pack_ids,
            "learning_foundation_ready": 15 in registry.ordered_pack_ids,
            "market_regime_before_decision": registry.dependency_sequence_ready,
            "execution_readiness_before_production": 18 in registry.ordered_pack_ids and 19 in registry.ordered_pack_ids,
            "production_integration_ready": 19 in registry.ordered_pack_ids,
            "deterministic_completion_report": True,
        }
        reason = decision.reasons[0] if decision.reasons else "milestone_c_completion_reported"
        return MilestoneCompletionReport(decision.status, registry.as_dict(), decision.as_dict(), audit, reason)
