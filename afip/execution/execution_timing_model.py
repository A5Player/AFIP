from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionTimingResult:
    status: str
    timing: str
    timing_score: float
    reason: str


class ExecutionTimingModel:
    """Assess execution timing from spread, liquidity, volatility, and decision confidence."""

    def evaluate(
        self,
        spread_points: float = 25.0,
        spread_limit: float = 35.0,
        volatility_state: str = "NORMAL",
        liquidity_state: str = "EXPANDING",
        decision_confidence: float = 0.80,
    ) -> ExecutionTimingResult:
        spread = max(float(spread_points or 0.0), 0.0)
        limit = max(float(spread_limit or 1.0), 1.0)
        confidence = self._ratio(decision_confidence)
        volatility = str(volatility_state or "NORMAL").upper()
        liquidity = str(liquidity_state or "NORMAL").upper()

        spread_score = max(0.0, 1.0 - (spread / limit))
        liquidity_score = 0.95 if liquidity in {"EXPANDING", "NORMAL"} else 0.55
        volatility_score = 0.68 if volatility in {"HIGH", "EXPANDING"} else 0.90
        timing_score = round((spread_score * 0.35) + (liquidity_score * 0.25) + (volatility_score * 0.15) + (confidence * 0.25), 4)

        if spread > limit or liquidity in {"CONTRACTING", "THIN"}:
            timing = "DELAY"
            status = "EXECUTION_TIMING_REVIEW"
            reason = "execution_cost_or_liquidity_review"
        elif timing_score >= 0.72 and confidence >= 0.75:
            timing = "IMMEDIATE"
            status = "EXECUTION_TIMING_READY"
            reason = "execution_timing_aligned"
        else:
            timing = "SELECTIVE"
            status = "EXECUTION_TIMING_SELECTIVE"
            reason = "selective_execution_timing"

        return ExecutionTimingResult(status=status, timing=timing, timing_score=timing_score, reason=reason)

    @staticmethod
    def _ratio(value: float) -> float:
        number = float(value or 0.0)
        if number > 1.0:
            number = number / 100.0
        return max(0.0, min(number, 1.0))
