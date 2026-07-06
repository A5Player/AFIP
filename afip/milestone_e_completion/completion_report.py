"""Final report model for Production Milestone E completion."""

from __future__ import annotations

from dataclasses import dataclass

from .completion_policy import MilestoneECompletionDecision
from .completion_registry import MilestoneECompletionRegistry


@dataclass(frozen=True)
class MilestoneECompletionReport:
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


class MilestoneECompletionReporter:
    def build(self, registry: MilestoneECompletionRegistry, decision: MilestoneECompletionDecision) -> MilestoneECompletionReport:
        ordered = set(registry.ordered_pack_ids)
        audit = {
            "session_intelligence_ready": 1 in ordered,
            "volatility_intelligence_ready": 2 in ordered,
            "market_memory_ready": 3 in ordered,
            "confidence_calibration_ready": 4 in ordered,
            "dynamic_weight_ready": 5 in ordered,
            "performance_attribution_ready": 6 in ordered,
            "portfolio_intelligence_ready": 7 in ordered,
            "macro_context_ready": 8 in ordered,
            "adaptive_learning_ready": 9 in ordered,
            "knowledge_first_ready": registry.knowledge_first_ready,
            "intelligence_sequence_ready": registry.intelligence_sequence_ready,
            "deterministic_completion_report": True,
        }
        reason = decision.reasons[0] if decision.reasons else "milestone_e_completion_reported"
        return MilestoneECompletionReport(decision.status, registry.as_dict(), decision.as_dict(), audit, reason)
