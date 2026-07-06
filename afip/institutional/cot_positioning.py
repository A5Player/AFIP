"""COT positioning assessment for gold market context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CotPositioningAssessment:
    """Compact COT assessment for long-term institutional positioning."""

    status: str
    positioning_bias: str
    confidence_score: float
    managed_money_net: float
    commercial_net: float
    open_interest: float
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "positioning_bias": self.positioning_bias,
            "confidence_score": self.confidence_score,
            "managed_money_net": self.managed_money_net,
            "commercial_net": self.commercial_net,
            "open_interest": self.open_interest,
            "reason": self.reason,
        }


class CotPositioningEngine:
    """Score COT values as strategic gold positioning context."""

    def assess(self, values: Mapping[str, object]) -> CotPositioningAssessment:
        managed_money_long = self._to_float(values.get("managed_money_long"))
        managed_money_short = self._to_float(values.get("managed_money_short"))
        commercial_long = self._to_float(values.get("commercial_long"))
        commercial_short = self._to_float(values.get("commercial_short"))
        open_interest = self._to_float(values.get("open_interest"))
        managed_money_net = managed_money_long - managed_money_short
        commercial_net = commercial_long - commercial_short
        scale = max(abs(managed_money_long) + abs(managed_money_short), 1.0)
        net_ratio = managed_money_net / scale

        if net_ratio >= 0.18:
            bias = "GOLD_SUPPORTIVE"
            confidence = min(96.0, 62.0 + abs(net_ratio) * 120.0)
            reason = "managed_money_net_long_positioning"
        elif net_ratio <= -0.18:
            bias = "GOLD_PRESSURE"
            confidence = min(96.0, 62.0 + abs(net_ratio) * 120.0)
            reason = "managed_money_net_short_positioning"
        else:
            bias = "NEUTRAL"
            confidence = 48.0
            reason = "cot_positioning_balanced"

        if open_interest <= 0:
            confidence = min(confidence, 50.0)
            reason = "cot_open_interest_missing"

        return CotPositioningAssessment(
            status="COT_POSITIONING_READY",
            positioning_bias=bias,
            confidence_score=round(confidence, 2),
            managed_money_net=round(managed_money_net, 2),
            commercial_net=round(commercial_net, 2),
            open_interest=round(open_interest, 2),
            reason=reason,
        )

    def assess_dict(self, values: Mapping[str, object]) -> dict[str, object]:
        return self.assess(values).as_dict()

    @staticmethod
    def _to_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
