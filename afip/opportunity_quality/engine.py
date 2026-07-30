from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence


WAIT = "WAIT"
ENTRY_ELIGIBLE = "ENTRY_ELIGIBLE"
HIGH_QUALITY = "HIGH_QUALITY"
ELITE = "ELITE"

ELIGIBLE_FOR_ADAPTIVE_SL_REVIEW = "ELIGIBLE_FOR_ADAPTIVE_SL_REVIEW"
NOT_ELIGIBLE = "NOT_ELIGIBLE"


@dataclass(frozen=True)
class OQSComponent:
    name: str
    score: float
    weight: float
    authority_approved: bool = True
    reason: str = ""

    def normalized(self) -> "OQSComponent":
        score = min(100.0, max(0.0, float(self.score)))
        weight = max(0.0, float(self.weight))
        return OQSComponent(
            name=str(self.name).strip(),
            score=score,
            weight=weight,
            authority_approved=bool(self.authority_approved),
            reason=str(self.reason or ""),
        )


@dataclass(frozen=True)
class PlanReviewInput:
    plan_id: str
    plan_status: str
    strategy_id: str
    strategy_status: str
    evidence_count: int
    sample_size: int
    all_authority_gates_passed: bool
    data_integrity_approved: bool
    components: Sequence[OQSComponent] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OQSAssessment:
    plan_id: str
    oqs: float
    quality_band: str
    status: str
    reason: str
    adaptive_sl_review_status: str
    component_scores: Mapping[str, float]
    execution_authority: bool = False
    order_send_called: bool = False


class OpportunityQualityEngine:
    """Advisory OQS runtime foundation.

    This engine may classify opportunity quality and indicate whether an
    opportunity can proceed to adaptive-SL review. It has no execution,
    position-sizing, capital, risk, or MT5 authority.
    """

    REQUIRED_PLAN_STATUS = "ELIGIBLE_FOR_OQS_REVIEW"
    REQUIRED_STRATEGY_STATUS = "ELIGIBLE_FOR_PLAN_REVIEW"

    def __init__(
        self,
        *,
        minimum_evidence_count: int = 5,
        minimum_sample_size: int = 30,
        minimum_oqs: float = 97.0,
        elite_oqs: float = 99.0,
    ) -> None:
        self.minimum_evidence_count = int(minimum_evidence_count)
        self.minimum_sample_size = int(minimum_sample_size)
        self.minimum_oqs = float(minimum_oqs)
        self.elite_oqs = float(elite_oqs)

    @staticmethod
    def _weighted_score(components: Iterable[OQSComponent]) -> tuple[float, dict[str, float], bool]:
        normalized = [c.normalized() for c in components]
        if not normalized:
            return 0.0, {}, False
        total_weight = sum(c.weight for c in normalized)
        if total_weight <= 0:
            return 0.0, {c.name: c.score for c in normalized}, False
        approved = all(c.authority_approved for c in normalized)
        value = sum(c.score * c.weight for c in normalized) / total_weight
        return round(value, 4), {c.name: c.score for c in normalized}, approved

    @staticmethod
    def classify(oqs: float) -> str:
        value = float(oqs)
        if value < 97.0:
            return WAIT
        if value < 98.0:
            return ENTRY_ELIGIBLE
        if value < 99.0:
            return HIGH_QUALITY
        return ELITE

    def assess(self, review: PlanReviewInput) -> OQSAssessment:
        score, component_scores, components_approved = self._weighted_score(review.components)

        def blocked(reason: str) -> OQSAssessment:
            return OQSAssessment(
                plan_id=review.plan_id,
                oqs=score,
                quality_band=self.classify(score),
                status=WAIT,
                reason=reason,
                adaptive_sl_review_status=NOT_ELIGIBLE,
                component_scores=component_scores,
            )

        if review.plan_status != self.REQUIRED_PLAN_STATUS:
            return blocked("plan_not_eligible_for_oqs_review")
        if review.strategy_status != self.REQUIRED_STRATEGY_STATUS:
            return blocked("strategy_not_eligible_for_plan_review")
        if not review.data_integrity_approved:
            return blocked("data_integrity_not_approved")
        if not review.all_authority_gates_passed:
            return blocked("authority_gate_not_approved")
        if not components_approved:
            return blocked("oqs_component_authority_not_approved")
        if review.evidence_count < self.minimum_evidence_count:
            return blocked("insufficient_evidence_count")
        if review.sample_size < self.minimum_sample_size:
            return blocked("insufficient_sample_size")
        if not component_scores:
            return blocked("oqs_components_missing")
        if score < self.minimum_oqs:
            return blocked("oqs_below_97")

        band = self.classify(score)
        adaptive = (
            ELIGIBLE_FOR_ADAPTIVE_SL_REVIEW
            if score >= self.elite_oqs
            else NOT_ELIGIBLE
        )
        return OQSAssessment(
            plan_id=review.plan_id,
            oqs=score,
            quality_band=band,
            status=band,
            reason="oqs_assessment_passed",
            adaptive_sl_review_status=adaptive,
            component_scores=component_scores,
        )
