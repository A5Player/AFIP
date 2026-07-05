"""Production Milestone A Pack 10: decision trace runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from afip.intelligence.decision_stability_index import DecisionStabilityIndex
from afip.intelligence.signal_persistence_analysis import SignalPersistenceAnalysis
from afip.learning.confidence_aggregation_refinement import ConfidenceAggregationRefinement


@dataclass(frozen=True)
class ProductionMilestoneADecisionTraceRuntimeResult:
    """Decision trace runtime result for production auditability."""

    status: str
    production_allowed: bool
    action: str
    trace_score: float
    decision_stability: Dict[str, Any]
    signal_persistence: Dict[str, Any]
    confidence_aggregation: Dict[str, Any]
    trace: list[Dict[str, Any]] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    reason: str = "production_decision_trace_runtime_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_allowed": self.production_allowed,
            "action": self.action,
            "trace_score": round(self.trace_score, 2),
            "decision_stability": dict(self.decision_stability),
            "signal_persistence": dict(self.signal_persistence),
            "confidence_aggregation": dict(self.confidence_aggregation),
            "trace": list(self.trace),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ProductionMilestoneADecisionTraceRuntime:
    """Coordinate decision stability, signal persistence, and confidence aggregation."""

    def evaluate(self, context: Mapping[str, Any]) -> ProductionMilestoneADecisionTraceRuntimeResult:
        stability_result = DecisionStabilityIndex().evaluate(context.get("decision_state", {})).to_dict()
        persistence_result = SignalPersistenceAnalysis().evaluate(context.get("signal_state", {})).to_dict()
        aggregation_result = ConfidenceAggregationRefinement().evaluate(context.get("confidence_state", {})).to_dict()

        blockers: list[str] = []
        for name, result in (
            ("decision_stability", stability_result),
            ("signal_persistence", persistence_result),
            ("confidence_aggregation", aggregation_result),
        ):
            for blocker in result.get("blockers", []):
                blockers.append(f"{name}:{blocker}")

        trace_score = (
            stability_result["stability_score"] * 0.34
            + persistence_result["persistence_score"] * 0.33
            + aggregation_result["refined_confidence"] * 0.33
        )
        production_allowed = trace_score >= 62.0 and not blockers
        action = _resolve_action(context, production_allowed)
        trace = _build_trace(stability_result, persistence_result, aggregation_result, trace_score, action)

        return ProductionMilestoneADecisionTraceRuntimeResult(
            status="READY" if production_allowed else "OBSERVE",
            production_allowed=production_allowed,
            action=action,
            trace_score=trace_score,
            decision_stability=stability_result,
            signal_persistence=persistence_result,
            confidence_aggregation=aggregation_result,
            trace=trace,
            blockers=blockers,
            reason="production_decision_trace_ready" if production_allowed else "production_decision_trace_observation_required",
        )


def _resolve_action(context: Mapping[str, Any], production_allowed: bool) -> str:
    if not production_allowed:
        return "HOLD"
    side = str(context.get("action", context.get("side", "BUY"))).upper()
    if side in {"BUY", "SELL"}:
        return side
    decision_state = context.get("decision_state", {})
    side = str(decision_state.get("side", decision_state.get("action", "BUY"))).upper()
    if side in {"BUY", "SELL"}:
        return side
    return "BUY"


def _build_trace(
    stability: Mapping[str, Any],
    persistence: Mapping[str, Any],
    aggregation: Mapping[str, Any],
    trace_score: float,
    action: str,
) -> list[Dict[str, Any]]:
    return [
        {
            "stage": "decision_stability",
            "score": stability["stability_score"],
            "status": stability["status"],
            "reason": stability["reason"],
        },
        {
            "stage": "signal_persistence",
            "score": persistence["persistence_score"],
            "status": persistence["status"],
            "reason": persistence["reason"],
        },
        {
            "stage": "confidence_aggregation",
            "score": aggregation["refined_confidence"],
            "status": aggregation["status"],
            "reason": aggregation["reason"],
        },
        {
            "stage": "runtime_decision",
            "score": round(trace_score, 2),
            "status": "READY" if action in {"BUY", "SELL"} else "OBSERVE",
            "reason": f"runtime_action_{action.lower()}",
        },
    ]
