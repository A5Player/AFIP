"""Production Milestone A Pack 2: market regime transition intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping


@dataclass(frozen=True)
class MarketRegimeTransitionResult:
    status: str
    transition: str
    stability_score: float
    risk_bias: str
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "transition": self.transition,
            "stability_score": round(self.stability_score, 2),
            "risk_bias": self.risk_bias,
            "reasons": list(self.reasons),
        }


class MarketRegimeTransitionIntelligence:
    """Detects whether the current financial regime is stable or changing."""

    def evaluate(self, regime_history: Iterable[Mapping[str, Any]]) -> MarketRegimeTransitionResult:
        history = list(regime_history)
        if len(history) < 3:
            return MarketRegimeTransitionResult(
                status="LEARNING",
                transition="UNKNOWN",
                stability_score=0.0,
                risk_bias="REDUCE_EXPOSURE",
                reasons=["insufficient_regime_history"],
            )

        regimes = [str(item.get("regime", "UNKNOWN")) for item in history[-6:]]
        current = regimes[-1]
        previous = regimes[-2]
        changes = sum(1 for left, right in zip(regimes, regimes[1:]) if left != right)
        stability_score = max(0.0, 100.0 - changes * 22.0)

        if current != previous:
            transition = f"{previous}_TO_{current}"
            risk_bias = "REDUCE_EXPOSURE"
            status = "CAUTION"
            reasons = ["current_regime_changed", f"changes:{changes}"]
        elif stability_score >= 70.0:
            transition = f"STABLE_{current}"
            risk_bias = "NORMAL_EXPOSURE"
            status = "READY"
            reasons = ["regime_stable"]
        else:
            transition = f"UNSTABLE_{current}"
            risk_bias = "REDUCE_EXPOSURE"
            status = "CAUTION"
            reasons = ["frequent_regime_changes", f"changes:{changes}"]

        return MarketRegimeTransitionResult(status, transition, stability_score, risk_bias, reasons)
