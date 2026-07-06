"""Open interest assessment for institutional participation context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class OpenInterestAssessment:
    """Open interest trend and participation quality assessment."""

    status: str
    participation_state: str
    confidence_score: float
    open_interest_change: float
    price_change: float
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "participation_state": self.participation_state,
            "confidence_score": self.confidence_score,
            "open_interest_change": self.open_interest_change,
            "price_change": self.price_change,
            "reason": self.reason,
        }


class OpenInterestRuntime:
    """Interpret open interest change together with price change."""

    def assess(self, values: Mapping[str, object]) -> OpenInterestAssessment:
        open_interest_change = self._to_float(values.get("open_interest_change"))
        price_change = self._to_float(values.get("gold_price_change"))
        abs_oi = abs(open_interest_change)
        confidence = min(94.0, 45.0 + abs_oi * 9.0)

        if open_interest_change > 0 and price_change > 0:
            state = "LONG_PARTICIPATION_EXPANDING"
            reason = "price_rising_with_open_interest_expansion"
        elif open_interest_change > 0 and price_change < 0:
            state = "SHORT_PARTICIPATION_EXPANDING"
            reason = "price_falling_with_open_interest_expansion"
        elif open_interest_change < 0 and price_change > 0:
            state = "SHORT_COVERING"
            reason = "price_rising_with_open_interest_contraction"
        elif open_interest_change < 0 and price_change < 0:
            state = "LONG_LIQUIDATION"
            reason = "price_falling_with_open_interest_contraction"
        else:
            state = "PARTICIPATION_BALANCED"
            confidence = 44.0
            reason = "open_interest_participation_balanced"

        return OpenInterestAssessment(
            status="OPEN_INTEREST_READY",
            participation_state=state,
            confidence_score=round(confidence, 2),
            open_interest_change=round(open_interest_change, 2),
            price_change=round(price_change, 2),
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
