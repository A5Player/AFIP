"""Runtime for Production Milestone C Pack 17 decision enhancement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .decision_context import DecisionContextBuilder
from .decision_evidence import DecisionEvidence
from .decision_policy import DecisionCandidate, DecisionSelectionPolicy
from .evidence_aggregator import DecisionEvidenceAggregator


@dataclass(frozen=True)
class EnhancedDecisionState:
    status: str
    context: dict[str, object]
    groups: list[dict[str, object]]
    decision: dict[str, object]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "context": dict(self.context),
            "groups": [dict(group) for group in self.groups],
            "decision": dict(self.decision),
            "reason": self.reason,
        }


class DecisionEnhancementRuntime:
    def __init__(self) -> None:
        self.context_builder = DecisionContextBuilder()
        self.aggregator = DecisionEvidenceAggregator()
        self.policy = DecisionSelectionPolicy()

    def run(self, regime_classification: Mapping[str, Any] | None, evidence_values: list[DecisionEvidence | Mapping[str, Any]]) -> EnhancedDecisionState:
        context = self.context_builder.build(regime_classification)
        if context.status != "DECISION_CONTEXT_READY":
            candidate = DecisionCandidate("WAIT", 0.0, 0.0, context.regime_first_key, tuple(context.reasons))
            return EnhancedDecisionState("DECISION_CONTEXT_DATA_REQUIRED", context.as_dict(), [], candidate.as_dict(), "market_regime_required")
        evidence = [item if isinstance(item, DecisionEvidence) else DecisionEvidence.from_mapping(item) for item in evidence_values]
        groups = self.aggregator.aggregate(context, evidence)
        candidate = self.policy.select(groups)
        status = "DECISION_INTELLIGENCE_READY" if candidate.action in {"BUY", "SELL"} else "DECISION_INTELLIGENCE_WAIT"
        return EnhancedDecisionState(status, context.as_dict(), [group.as_dict() for group in groups], candidate.as_dict(), str(candidate.reasons[0]))
