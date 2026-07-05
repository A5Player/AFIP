"""Score fusion utilities for AFIP Production Milestone B Pack 1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class IntelligenceScoreFusionResult:
    """Weighted score fusion result."""

    status: str
    action: str
    buy_score: float
    sell_score: float
    flat_score: float
    confidence: float
    direction: str
    reason: str


class IntelligenceScoreFusion:
    """Fuse weighted market intelligence scores into one financial direction."""

    def fuse(self, signals: Iterable[Mapping[str, float | str]]) -> IntelligenceScoreFusionResult:
        """Return a deterministic weighted direction from financial signal inputs."""
        buy_total = 0.0
        sell_total = 0.0
        flat_total = 0.0
        weight_total = 0.0

        for signal in signals:
            direction = str(signal.get("direction", "FLAT")).upper()
            confidence = self._ratio(float(signal.get("confidence", 0.0)))
            weight = max(0.0, float(signal.get("weight", 1.0)))
            contribution = confidence * weight
            weight_total += weight

            if direction == "BUY":
                buy_total += contribution
            elif direction == "SELL":
                sell_total += contribution
            else:
                flat_total += contribution

        if weight_total <= 0.0:
            return IntelligenceScoreFusionResult(
                status="FUSION_INPUT_EMPTY",
                action="KEEP_SIMULATION_ONLY",
                buy_score=0.0,
                sell_score=0.0,
                flat_score=0.0,
                confidence=0.0,
                direction="FLAT",
                reason="no_weighted_financial_signal_input",
            )

        active_total = buy_total + sell_total + flat_total
        if active_total <= 0.0:
            return IntelligenceScoreFusionResult(
                status="FUSION_SCORE_NEUTRAL",
                action="KEEP_SIMULATION_ONLY",
                buy_score=0.0,
                sell_score=0.0,
                flat_score=0.0,
                confidence=0.0,
                direction="FLAT",
                reason="no_active_weighted_financial_signal_input",
            )

        buy_score = round(buy_total / active_total * 100.0, 2)
        sell_score = round(sell_total / active_total * 100.0, 2)
        flat_score = round(flat_total / active_total * 100.0, 2)
        direction_scores = {"BUY": buy_score, "SELL": sell_score, "FLAT": flat_score}
        direction = max(direction_scores, key=direction_scores.get)
        confidence = direction_scores[direction]

        if confidence >= 70.0:
            status = "FUSION_SCORE_READY"
            action = "ACCEPT_FUSED_FINANCIAL_DIRECTION"
            reason = "dominant_weighted_direction"
        elif confidence >= 50.0:
            status = "FUSION_SCORE_REVIEW"
            action = "REVIEW_FUSED_FINANCIAL_DIRECTION"
            reason = "moderate_weighted_direction"
        else:
            status = "FUSION_SCORE_NEUTRAL"
            action = "KEEP_SIMULATION_ONLY"
            reason = "insufficient_weighted_direction"

        return IntelligenceScoreFusionResult(
            status=status,
            action=action,
            buy_score=buy_score,
            sell_score=sell_score,
            flat_score=flat_score,
            confidence=round(confidence, 2),
            direction=direction,
            reason=reason,
        )

    @staticmethod
    def _ratio(value: float) -> float:
        """Normalize a score into a zero-to-one confidence ratio."""
        if value > 1.0:
            value = value / 100.0
        return min(max(value, 0.0), 1.0)
