from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any

NOT_ELIGIBLE = "NOT_ELIGIBLE"
NORMAL_SL_APPROVED = "NORMAL_SL_APPROVED"
EXTENDED_SL_APPROVED = "EXTENDED_SL_APPROVED"


@dataclass(frozen=True)
class AdaptiveSLInput:
    plan_id: str
    oqs: float
    oqs_status: str
    adaptive_sl_review_status: str
    final_confidence: float
    evidence_quality: str
    capital_pass: bool
    risk_pass: bool
    execution_pass: bool
    reward_risk_pass: bool
    data_integrity_pass: bool
    atr_points: float
    structure_points: float
    buffer_points: float
    requested_sl_points: float | None = None
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class AdaptiveSLAssessment:
    plan_id: str
    status: str
    reason: str
    sl_mode: str
    recommended_sl_points: int | None
    hard_ceiling_points: int | None
    execution_authority: bool = False
    order_send_called: bool = False


class AdaptiveSLRuntime:
    """Advisory-only Adaptive SL policy evaluator."""

    HARD_CEILING = None

    def _base_distance(self, item: AdaptiveSLInput) -> float:
        derived = max(
            0.0,
            float(item.atr_points) + float(item.buffer_points),
            float(item.structure_points) + float(item.buffer_points),
        )
        if item.requested_sl_points is not None:
            derived = max(derived, float(item.requested_sl_points))
        return derived

    @staticmethod
    def _all_common_gates_pass(item: AdaptiveSLInput) -> bool:
        return all((
            item.capital_pass,
            item.risk_pass,
            item.execution_pass,
            item.reward_risk_pass,
            item.data_integrity_pass,
        ))

    def assess(self, item: AdaptiveSLInput) -> AdaptiveSLAssessment:
        def blocked(reason: str) -> AdaptiveSLAssessment:
            return AdaptiveSLAssessment(
                plan_id=item.plan_id,
                status=NOT_ELIGIBLE,
                reason=reason,
                sl_mode="NONE",
                recommended_sl_points=None,
                hard_ceiling_points=self.HARD_CEILING,
            )

        if not self._all_common_gates_pass(item):
            return blocked("required_gate_not_approved")
        if str(item.adaptive_sl_review_status).strip().upper() != "ELIGIBLE_FOR_ADAPTIVE_SL_REVIEW":
            return blocked("research_standard_review_not_approved")

        base = self._base_distance(item)
        if base <= 0:
            return blocked("invalid_sl_distance")

        if str(item.oqs_status).strip().upper() in {"", "WAIT_OR_SKIP"}:
            return blocked("opportunity_not_eligible_for_plan_review")
        recommended = round(base)
        return AdaptiveSLAssessment(
            plan_id=item.plan_id,
            status=NORMAL_SL_APPROVED,
            reason="structure_atr_research_buffer_policy_passed",
            sl_mode="STRUCTURE_ATR_RESEARCH_BUFFER",
            recommended_sl_points=int(recommended),
            hard_ceiling_points=self.HARD_CEILING,
        )
