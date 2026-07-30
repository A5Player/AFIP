from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

WAIT_DATA = "WAIT_DATA"
HOLD = "HOLD"
PROTECT_PROFIT = "PROTECT_PROFIT"
REDUCE_EXPOSURE = "REDUCE_EXPOSURE"
EXIT_REVIEW = "EXIT_REVIEW"


@dataclass(frozen=True)
class HoldingContext:
    position_id: str
    adaptive_sl_status: str
    data_integrity_pass: bool
    risk_pass: bool
    execution_pass: bool
    trend_continuity_score: float
    structure_integrity_score: float
    regime_stability_score: float
    momentum_score: float
    exit_evidence_score: float
    mfe_points: float
    mae_points: float
    unrealized_points: float
    protected_points: float
    holding_minutes: int
    expected_holding_minutes: int
    news_risk_high: bool = False
    spread_abnormal: bool = False
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class HoldingAssessment:
    position_id: str
    action: str
    reason: str
    holding_quality_score: float
    protection_ratio: float
    adverse_ratio: float
    order_modify_called: bool = False
    order_close_called: bool = False
    execution_authority: bool = False


class HoldingIntelligenceRuntime:
    """Advisory-only position holding intelligence.

    It evaluates whether the evidence supports holding, protecting profit,
    reducing exposure, or escalating to exit review. It never modifies or
    closes an order.
    """

    ACCEPTED_ADAPTIVE_SL = {"NORMAL_SL_APPROVED", "EXTENDED_SL_APPROVED"}

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    def _quality_score(self, item: HoldingContext) -> float:
        score = (
            self._clip(item.trend_continuity_score) * 0.25
            + self._clip(item.structure_integrity_score) * 0.25
            + self._clip(item.regime_stability_score) * 0.20
            + self._clip(item.momentum_score) * 0.15
            + (100.0 - self._clip(item.exit_evidence_score)) * 0.15
        )
        return round(score, 4)

    @staticmethod
    def _protection_ratio(item: HoldingContext) -> float:
        if item.unrealized_points <= 0:
            return 0.0
        return round(max(0.0, float(item.protected_points)) / float(item.unrealized_points), 4)

    @staticmethod
    def _adverse_ratio(item: HoldingContext) -> float:
        denominator = max(1.0, abs(float(item.mfe_points)))
        return round(max(0.0, abs(float(item.mae_points))) / denominator, 4)

    def assess(self, item: HoldingContext) -> HoldingAssessment:
        quality = self._quality_score(item)
        protection = self._protection_ratio(item)
        adverse = self._adverse_ratio(item)

        def result(action: str, reason: str) -> HoldingAssessment:
            return HoldingAssessment(
                position_id=item.position_id,
                action=action,
                reason=reason,
                holding_quality_score=quality,
                protection_ratio=protection,
                adverse_ratio=adverse,
            )

        if item.adaptive_sl_status not in self.ACCEPTED_ADAPTIVE_SL:
            return result(WAIT_DATA, "adaptive_sl_not_approved")
        if not item.data_integrity_pass:
            return result(WAIT_DATA, "data_integrity_not_approved")
        if not item.risk_pass or not item.execution_pass:
            return result(EXIT_REVIEW, "independent_authority_not_approved")

        if item.news_risk_high or item.spread_abnormal:
            return result(PROTECT_PROFIT, "market_risk_protection_required")

        expected = max(1, int(item.expected_holding_minutes))
        time_ratio = max(0.0, float(item.holding_minutes)) / expected

        if (
            item.exit_evidence_score >= 80
            or item.structure_integrity_score < 35
            or item.regime_stability_score < 35
            or adverse >= 0.85
        ):
            return result(EXIT_REVIEW, "exit_evidence_dominant")

        if (
            item.exit_evidence_score >= 60
            or item.trend_continuity_score < 50
            or item.structure_integrity_score < 50
            or time_ratio >= 2.0
        ):
            return result(REDUCE_EXPOSURE, "holding_evidence_degraded")

        if item.unrealized_points > 0 and (
            protection < 0.35
            or item.mfe_points >= 500
            or time_ratio >= 1.25
        ):
            return result(PROTECT_PROFIT, "profit_protection_required")

        if quality >= 70 and item.exit_evidence_score < 45:
            return result(HOLD, "holding_evidence_supported")

        return result(PROTECT_PROFIT, "mixed_holding_evidence")
