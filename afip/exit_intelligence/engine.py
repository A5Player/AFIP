from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

WAIT_DATA = "WAIT_DATA"
MONITOR = "MONITOR"
PARTIAL_EXIT_REVIEW = "PARTIAL_EXIT_REVIEW"
FULL_EXIT_REVIEW = "FULL_EXIT_REVIEW"

@dataclass(frozen=True)
class ExitReviewInput:
    position_id: str
    holding_action: str
    data_integrity_pass: bool
    risk_pass: bool
    execution_pass: bool
    structure_break_score: float
    regime_reversal_score: float
    momentum_failure_score: float
    time_decay_score: float
    profit_giveback_ratio: float
    exit_evidence_score: float
    unrealized_points: float
    protected_points: float
    metadata: Mapping[str, Any] | None = None

@dataclass(frozen=True)
class ExitReviewAssessment:
    position_id: str
    status: str
    reason: str
    exit_pressure_score: float
    primary_driver: str
    order_close_called: bool = False
    partial_close_called: bool = False
    execution_authority: bool = False

class ExitIntelligenceRuntime:
    ACCEPTED_HOLDING_ACTIONS = {"REDUCE_EXPOSURE", "EXIT_REVIEW"}

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    def _pressure(self, item: ExitReviewInput) -> tuple[float, str]:
        components = {
            "STRUCTURE_BREAK": self._clip(item.structure_break_score),
            "REGIME_REVERSAL": self._clip(item.regime_reversal_score),
            "MOMENTUM_FAILURE": self._clip(item.momentum_failure_score),
            "TIME_DECAY": self._clip(item.time_decay_score),
            "PROFIT_GIVEBACK": self._clip(item.profit_giveback_ratio * 100.0),
            "EXIT_EVIDENCE": self._clip(item.exit_evidence_score),
        }
        weights = {
            "STRUCTURE_BREAK": 0.25,
            "REGIME_REVERSAL": 0.20,
            "MOMENTUM_FAILURE": 0.15,
            "TIME_DECAY": 0.10,
            "PROFIT_GIVEBACK": 0.15,
            "EXIT_EVIDENCE": 0.15,
        }
        score = sum(components[k] * weights[k] for k in components)
        driver = max(components, key=components.get)
        return round(score, 4), driver

    def assess(self, item: ExitReviewInput) -> ExitReviewAssessment:
        pressure, driver = self._pressure(item)

        def result(status: str, reason: str) -> ExitReviewAssessment:
            return ExitReviewAssessment(
                position_id=item.position_id,
                status=status,
                reason=reason,
                exit_pressure_score=pressure,
                primary_driver=driver,
            )

        if item.holding_action not in self.ACCEPTED_HOLDING_ACTIONS:
            return result(WAIT_DATA, "holding_action_not_eligible")
        if not item.data_integrity_pass:
            return result(WAIT_DATA, "data_integrity_not_approved")
        if not item.risk_pass or not item.execution_pass:
            return result(FULL_EXIT_REVIEW, "independent_authority_failure")

        giveback = max(0.0, float(item.profit_giveback_ratio))
        protected = max(0.0, float(item.protected_points))
        unrealized = float(item.unrealized_points)

        if (
            item.structure_break_score >= 80
            or item.regime_reversal_score >= 85
            or item.exit_evidence_score >= 85
            or pressure >= 80
        ):
            return result(FULL_EXIT_REVIEW, "dominant_exit_evidence")

        if (
            item.structure_break_score >= 60
            or item.regime_reversal_score >= 60
            or item.momentum_failure_score >= 65
            or giveback >= 0.50
            or pressure >= 60
        ):
            return result(PARTIAL_EXIT_REVIEW, "material_exit_pressure")

        if unrealized > 0 and protected < unrealized * 0.35:
            return result(PARTIAL_EXIT_REVIEW, "profit_insufficiently_protected")

        return result(MONITOR, "exit_pressure_not_dominant")
