"""Production Milestone A Pack 10: decision stability index."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping


@dataclass(frozen=True)
class DecisionStabilityIndexResult:
    """Decision stability result for production runtime quality."""

    status: str
    production_ready: bool
    stability_score: float
    stability_state: str
    directional_alignment: float
    confidence_stability: float
    regime_alignment: float
    execution_alignment: float
    blockers: list[str] = field(default_factory=list)
    reason: str = "decision_stability_index_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_ready": self.production_ready,
            "stability_score": round(self.stability_score, 2),
            "stability_state": self.stability_state,
            "directional_alignment": round(self.directional_alignment, 2),
            "confidence_stability": round(self.confidence_stability, 2),
            "regime_alignment": round(self.regime_alignment, 2),
            "execution_alignment": round(self.execution_alignment, 2),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class DecisionStabilityIndex:
    """Evaluate whether recent production decisions remain stable enough to act."""

    def evaluate(self, decision_state: Mapping[str, Any]) -> DecisionStabilityIndexResult:
        decisions = list(decision_state.get("recent_decisions", []))
        current_side = str(decision_state.get("side", decision_state.get("action", "BUY"))).upper()

        directional_alignment = _directional_alignment(decisions, current_side)
        confidence_stability = _bounded(decision_state.get("confidence_stability", _confidence_stability(decisions)))
        regime_alignment = _bounded(decision_state.get("regime_alignment", 50.0))
        execution_alignment = _bounded(decision_state.get("execution_alignment", decision_state.get("execution_quality", 50.0)))

        stability_score = (
            directional_alignment * 0.30
            + confidence_stability * 0.25
            + regime_alignment * 0.25
            + execution_alignment * 0.20
        )

        blockers: list[str] = []
        if directional_alignment < 58.0:
            blockers.append("directional_alignment_below_decision_threshold")
        if confidence_stability < 55.0:
            blockers.append("confidence_stability_below_decision_threshold")
        if regime_alignment < 55.0:
            blockers.append("regime_alignment_below_decision_threshold")
        if execution_alignment < 50.0:
            blockers.append("execution_alignment_below_decision_threshold")

        production_ready = stability_score >= 62.0 and not blockers
        if stability_score >= 84.0:
            stability_state = "HIGH_STABILITY"
        elif stability_score >= 62.0:
            stability_state = "STANDARD_STABILITY"
        else:
            stability_state = "LOW_STABILITY"

        return DecisionStabilityIndexResult(
            status="READY" if production_ready else "OBSERVE",
            production_ready=production_ready,
            stability_score=stability_score,
            stability_state=stability_state,
            directional_alignment=directional_alignment,
            confidence_stability=confidence_stability,
            regime_alignment=regime_alignment,
            execution_alignment=execution_alignment,
            blockers=blockers,
            reason="decision_stability_ready" if production_ready else "decision_stability_observation_required",
        )


def _directional_alignment(decisions: Iterable[Mapping[str, Any]], current_side: str) -> float:
    rows = list(decisions)
    if not rows:
        return 50.0
    valid_sides = {"BUY", "SELL", "HOLD"}
    aligned = 0
    total = 0
    for row in rows:
        side = str(row.get("side", row.get("action", ""))).upper()
        if side not in valid_sides:
            continue
        total += 1
        if side == current_side:
            aligned += 1
    if total == 0:
        return 50.0
    return (aligned / total) * 100.0


def _confidence_stability(decisions: Iterable[Mapping[str, Any]]) -> float:
    values = [_bounded(row.get("confidence", row.get("entry_score", 50.0))) for row in decisions]
    if len(values) < 2:
        return values[0] if values else 50.0
    mean_value = sum(values) / len(values)
    average_deviation = sum(abs(value - mean_value) for value in values) / len(values)
    return max(0.0, 100.0 - average_deviation * 3.0)


def _bounded(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 50.0
    return max(0.0, min(100.0, numeric))
