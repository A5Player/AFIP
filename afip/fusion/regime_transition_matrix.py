from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RegimeTransitionResult:
    status: str
    previous_regime: str
    current_regime: str
    transition_risk: float
    stability_score: float
    reason: str


class RegimeTransitionMatrix:
    """Evaluate transition risk between market regimes using financial terminology."""

    _SAME_REGIME_RISK = 0.12
    _TRANSITION_RISK: Mapping[tuple[str, str], float] = {
        ("TREND", "RANGE"): 0.48,
        ("RANGE", "TREND"): 0.42,
        ("TREND", "HIGH_VOLATILITY"): 0.72,
        ("RANGE", "HIGH_VOLATILITY"): 0.68,
        ("HIGH_VOLATILITY", "TREND"): 0.55,
        ("HIGH_VOLATILITY", "RANGE"): 0.50,
        ("NEWS", "HIGH_VOLATILITY"): 0.84,
        ("HIGH_VOLATILITY", "NEWS"): 0.88,
        ("TREND", "NEWS"): 0.90,
        ("RANGE", "NEWS"): 0.86,
    }

    def evaluate(self, previous_regime: str, current_regime: str) -> RegimeTransitionResult:
        previous = (previous_regime or "BALANCED").upper()
        current = (current_regime or "BALANCED").upper()
        if previous == current:
            transition_risk = self._SAME_REGIME_RISK
            reason = "regime_continuity"
        else:
            transition_risk = self._TRANSITION_RISK.get((previous, current), 0.58)
            reason = "regime_transition_detected"
        stability_score = round(max(0.0, 1.0 - transition_risk), 4)
        status = "REGIME_TRANSITION_READY" if stability_score >= 0.25 else "REGIME_TRANSITION_REVIEW"
        return RegimeTransitionResult(status, previous, current, round(transition_risk, 4), stability_score, reason)
