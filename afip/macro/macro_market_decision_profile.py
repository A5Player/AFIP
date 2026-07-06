"""Decision profile for integrated macro market consensus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class MacroMarketDecisionProfile:
    """Financial decision profile derived from macro market consensus."""

    status: str
    exposure_instruction: str
    position_horizon: str
    review_required: bool
    confidence_floor: float
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "exposure_instruction": self.exposure_instruction,
            "position_horizon": self.position_horizon,
            "review_required": self.review_required,
            "confidence_floor": self.confidence_floor,
            "reason": self.reason,
        }


class MacroMarketDecisionProfileEngine:
    """Translate consensus conditions into a clean financial exposure profile."""

    def build(self, consensus: Mapping[str, object]) -> MacroMarketDecisionProfile:
        bias = str(consensus.get("gold_market_bias", "NEUTRAL"))
        score = self._to_float(consensus.get("macro_score"), 50.0)
        confidence = self._to_float(consensus.get("decision_confidence"), 0.0)
        risk_state = str(consensus.get("event_risk_state", "CLEAR"))
        conflict_level = str(consensus.get("conflict_level", "LOW"))
        news_impact = self._to_float(consensus.get("news_impact_score"), 0.0)

        if risk_state == "RESTRICTED":
            return MacroMarketDecisionProfile(
                status="MACRO_MARKET_DECISION_PROFILE_READY",
                exposure_instruction="NO_NEW_EXPOSURE",
                position_horizon="INTRADAY_REVIEW",
                review_required=True,
                confidence_floor=95.0,
                reason="restricted_calendar_window",
            )
        if conflict_level == "HIGH" or bias == "MIXED":
            return MacroMarketDecisionProfile(
                status="MACRO_MARKET_DECISION_PROFILE_READY",
                exposure_instruction="REVIEW_ONLY",
                position_horizon="INTRADAY_REVIEW",
                review_required=True,
                confidence_floor=85.0,
                reason="macro_components_conflict",
            )
        if news_impact >= 90.0 and confidence < 80.0:
            return MacroMarketDecisionProfile(
                status="MACRO_MARKET_DECISION_PROFILE_READY",
                exposure_instruction="REDUCE_NEW_EXPOSURE",
                position_horizon="INTRADAY_ONLY",
                review_required=True,
                confidence_floor=80.0,
                reason="high_impact_news_requires_confirmation",
            )
        if bias == "GOLD_SUPPORTIVE" and score >= 63.0:
            return MacroMarketDecisionProfile(
                status="MACRO_MARKET_DECISION_PROFILE_READY",
                exposure_instruction="FAVOR_LONG_EXPOSURE",
                position_horizon="DAY_TRADE_PREFERRED",
                review_required=False,
                confidence_floor=70.0,
                reason="supportive_macro_alignment",
            )
        if bias == "GOLD_PRESSURE" and score <= 37.0:
            return MacroMarketDecisionProfile(
                status="MACRO_MARKET_DECISION_PROFILE_READY",
                exposure_instruction="REDUCE_LONG_EXPOSURE",
                position_horizon="DAY_TRADE_PREFERRED",
                review_required=False,
                confidence_floor=70.0,
                reason="pressuring_macro_alignment",
            )
        return MacroMarketDecisionProfile(
            status="MACRO_MARKET_DECISION_PROFILE_READY",
            exposure_instruction="BALANCED_REVIEW",
            position_horizon="INTRADAY_REVIEW",
            review_required=False,
            confidence_floor=75.0,
            reason="balanced_macro_conditions",
        )

    @staticmethod
    def _to_float(value: object, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
