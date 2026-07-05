"""Production Milestone A Pack 9: execution consistency index."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class ExecutionConsistencyIndexResult:
    """Execution consistency result for production decision quality."""

    status: str
    production_ready: bool
    consistency_score: float
    consistency_state: str
    fill_consistency: float
    spread_consistency: float
    slippage_consistency: float
    decision_consistency: float
    blockers: list[str] = field(default_factory=list)
    reason: str = "execution_consistency_index_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_ready": self.production_ready,
            "consistency_score": round(self.consistency_score, 2),
            "consistency_state": self.consistency_state,
            "fill_consistency": round(self.fill_consistency, 2),
            "spread_consistency": round(self.spread_consistency, 2),
            "slippage_consistency": round(self.slippage_consistency, 2),
            "decision_consistency": round(self.decision_consistency, 2),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ExecutionConsistencyIndex:
    """Evaluate whether execution quality is consistent enough for production."""

    def evaluate(self, execution_state: Mapping[str, Any]) -> ExecutionConsistencyIndexResult:
        fill_consistency = _bounded(execution_state.get("fill_consistency", execution_state.get("fill_probability", 50.0)))
        spread_consistency = _bounded(execution_state.get("spread_consistency", execution_state.get("spread_quality", 50.0)))
        slippage_consistency = _bounded(execution_state.get("slippage_consistency", execution_state.get("slippage_quality", 50.0)))
        decision_consistency = _bounded(execution_state.get("decision_consistency", execution_state.get("signal_consistency", 50.0)))

        consistency_score = (
            fill_consistency * 0.30
            + spread_consistency * 0.25
            + slippage_consistency * 0.20
            + decision_consistency * 0.25
        )

        blockers: list[str] = []
        if fill_consistency < 58.0:
            blockers.append("fill_consistency_below_execution_threshold")
        if spread_consistency < 55.0:
            blockers.append("spread_consistency_below_execution_threshold")
        if slippage_consistency < 50.0:
            blockers.append("slippage_consistency_below_execution_threshold")
        if decision_consistency < 60.0:
            blockers.append("decision_consistency_below_execution_threshold")

        production_ready = consistency_score >= 62.0 and not blockers
        if consistency_score >= 84.0:
            consistency_state = "HIGH_CONSISTENCY"
        elif consistency_score >= 62.0:
            consistency_state = "STANDARD_CONSISTENCY"
        else:
            consistency_state = "LOW_CONSISTENCY"

        return ExecutionConsistencyIndexResult(
            status="READY" if production_ready else "OBSERVE",
            production_ready=production_ready,
            consistency_score=consistency_score,
            consistency_state=consistency_state,
            fill_consistency=fill_consistency,
            spread_consistency=spread_consistency,
            slippage_consistency=slippage_consistency,
            decision_consistency=decision_consistency,
            blockers=blockers,
            reason="execution_consistency_ready" if production_ready else "execution_consistency_observation_required",
        )


def _bounded(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 50.0
    return max(0.0, min(100.0, numeric))
