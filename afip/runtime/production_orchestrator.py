"""Production orchestration layer for AFIP decision, risk, and reporting modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProductionOrchestrationResult:
    status: str
    action: str
    confidence: float
    readiness_score: float
    risk_score: float
    reason: str
    payload: dict[str, Any]


class ProductionOrchestrator:
    """Coordinate deterministic production decision components."""

    def run(
        self,
        decision: dict[str, Any],
        readiness: dict[str, Any] | None = None,
        risk: dict[str, Any] | None = None,
        checkpoint: dict[str, Any] | None = None,
    ) -> ProductionOrchestrationResult:
        readiness = readiness or {}
        risk = risk or {}
        checkpoint = checkpoint or {}

        action = str(decision.get("action", "WAIT"))
        confidence = self._bounded_float(decision.get("confidence", 0.0))
        readiness_score = self._bounded_float(readiness.get("score", readiness.get("readiness_score", 0.0)))
        risk_score = self._bounded_float(risk.get("score", risk.get("risk_score", 0.0)))
        checkpoint_status = str(checkpoint.get("status", "PASS"))

        blocked_reasons: list[str] = []
        if action not in {"BUY", "SELL"}:
            blocked_reasons.append("no_trade_action")
        if confidence < 65:
            blocked_reasons.append("confidence_below_threshold")
        if readiness_score < 70:
            blocked_reasons.append("readiness_below_threshold")
        if risk_score < 60:
            blocked_reasons.append("risk_score_below_threshold")
        if checkpoint_status != "PASS":
            blocked_reasons.append("quality_checkpoint_not_passed")

        status = "READY" if not blocked_reasons else "WAIT"
        reason = "production_orchestration_ready" if status == "READY" else ";".join(blocked_reasons)

        payload = {
            "decision": decision,
            "readiness": readiness,
            "risk": risk,
            "checkpoint": checkpoint,
            "blocked_reasons": tuple(blocked_reasons),
        }

        return ProductionOrchestrationResult(
            status=status,
            action=action if status == "READY" else "WAIT",
            confidence=confidence,
            readiness_score=readiness_score,
            risk_score=risk_score,
            reason=reason,
            payload=payload,
        )

    @staticmethod
    def _bounded_float(value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 0.0
        return round(max(0.0, min(100.0, number)), 2)
