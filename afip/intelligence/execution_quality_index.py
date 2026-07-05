"""Production Milestone A Pack 5: execution quality index."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class ExecutionQualityIndexResult:
    """Execution quality score for spread, liquidity, and decision readiness."""

    status: str
    execution_quality_score: float
    cost_status: str
    liquidity_status: str
    decision_status: str
    blockers: list[str] = field(default_factory=list)
    reason: str = "execution_quality_index_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "execution_quality_score": round(self.execution_quality_score, 2),
            "cost_status": self.cost_status,
            "liquidity_status": self.liquidity_status,
            "decision_status": self.decision_status,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ExecutionQualityIndex:
    """Scores execution readiness without placing orders or changing live state."""

    def evaluate(self, context: Mapping[str, Any]) -> ExecutionQualityIndexResult:
        cost_quality = context.get("cost_quality", {}) or {}
        liquidity_quality = context.get("liquidity_quality", {}) or {}
        decision_quality = context.get("decision_quality", {}) or {}

        spread_quality = float(cost_quality.get("spread_quality", context.get("spread_quality", 0.0)))
        slippage_quality = float(cost_quality.get("slippage_quality", context.get("slippage_quality", spread_quality)))
        liquidity_score = float(liquidity_quality.get("liquidity_score", context.get("liquidity_score", 0.0)))
        fill_probability = float(liquidity_quality.get("fill_probability", context.get("fill_probability", liquidity_score)))
        decision_confidence = float(decision_quality.get("confidence", context.get("confidence", 0.0)))
        signal_consistency = float(decision_quality.get("signal_consistency", context.get("signal_consistency", decision_confidence)))

        cost_score = (spread_quality * 0.65) + (slippage_quality * 0.35)
        liquidity_component = (liquidity_score * 0.60) + (fill_probability * 0.40)
        decision_component = (decision_confidence * 0.70) + (signal_consistency * 0.30)
        total_score = (cost_score * 0.35) + (liquidity_component * 0.30) + (decision_component * 0.35)
        total_score = max(0.0, min(100.0, total_score))

        blockers: list[str] = []
        if cost_score < 55.0:
            blockers.append("execution_cost_quality_low")
        if liquidity_component < 55.0:
            blockers.append("liquidity_quality_low")
        if decision_component < 55.0:
            blockers.append("decision_quality_low")

        return ExecutionQualityIndexResult(
            status="READY" if not blockers else "OBSERVE",
            execution_quality_score=total_score,
            cost_status="READY" if cost_score >= 55.0 else "OBSERVE",
            liquidity_status="READY" if liquidity_component >= 55.0 else "OBSERVE",
            decision_status="READY" if decision_component >= 55.0 else "OBSERVE",
            blockers=blockers,
            reason="execution_quality_index_ready" if not blockers else "execution_quality_index_protective_observation",
        )
