"""Production Milestone A1: Adaptive Intelligence Core.

This module is intentionally dependency-free and additive. It can be used by
existing AFIP runtime layers without changing older public contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

_VALID_SIDES = {"BUY", "SELL", "HOLD", "NEUTRAL", None}
_READY_STATUSES = {"READY", "ESTIMATED", "LEARNING"}


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    """Clamp a numeric value into an inclusive range."""
    return max(minimum, min(maximum, float(value)))


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class AdaptiveSignal:
    """Normalized financial intelligence input for adaptive aggregation."""

    name: str
    group: str = "general"
    side: Optional[str] = "NEUTRAL"
    score: float = 50.0
    confidence: float = 50.0
    weight: float = 1.0
    status: str = "READY"
    reason: str = "signal_normalized"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "AdaptiveSignal":
        """Build a signal from older dict-style AFIP intelligence outputs."""
        side = payload.get("side", payload.get("action", "NEUTRAL"))
        if side not in _VALID_SIDES:
            side = "NEUTRAL"
        return cls(
            name=str(payload.get("name", payload.get("engine", "unknown_signal"))),
            group=str(payload.get("group", "general")),
            side=side,
            score=clamp(_as_float(payload.get("score", payload.get("confidence", 50.0)), 50.0)),
            confidence=clamp(_as_float(payload.get("confidence", payload.get("score", 50.0)), 50.0)),
            weight=max(0.0, _as_float(payload.get("weight", 1.0), 1.0)),
            status=str(payload.get("status", "READY")),
            reason=str(payload.get("reason", "signal_normalized")),
            metadata=dict(payload.get("data", payload.get("metadata", {})) or {}),
        )


@dataclass(frozen=True)
class AdaptiveDecision:
    """Production-safe output from the adaptive aggregation layer."""

    status: str
    action: str
    confidence: float
    buy_score: float
    sell_score: float
    hold_score: float
    readiness: float
    signal_count: int
    reasons: List[str]
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "action": self.action,
            "confidence": round(self.confidence, 2),
            "buy_score": round(self.buy_score, 2),
            "sell_score": round(self.sell_score, 2),
            "hold_score": round(self.hold_score, 2),
            "readiness": round(self.readiness, 2),
            "signal_count": self.signal_count,
            "reasons": list(self.reasons),
            "diagnostics": dict(self.diagnostics),
        }


class AdaptiveIntelligenceCore:
    """Weighted financial intelligence aggregation with safe defaults."""

    def __init__(self, min_confidence: float = 60.0, decision_margin: float = 7.5) -> None:
        self.min_confidence = clamp(min_confidence)
        self.decision_margin = max(0.0, float(decision_margin))

    def evaluate(self, signals: Iterable[AdaptiveSignal | Mapping[str, Any]], context: Optional[Mapping[str, Any]] = None) -> AdaptiveDecision:
        normalized = [s if isinstance(s, AdaptiveSignal) else AdaptiveSignal.from_mapping(s) for s in signals]
        if not normalized:
            return AdaptiveDecision(
                status="OBSERVE",
                action="HOLD",
                confidence=0.0,
                buy_score=0.0,
                sell_score=0.0,
                hold_score=100.0,
                readiness=0.0,
                signal_count=0,
                reasons=["no_adaptive_signals"],
                diagnostics={"context": dict(context or {})},
            )

        score_buckets = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        weight_buckets = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        readiness_weight = 0.0
        readiness_total = 0.0
        reasons: List[str] = []

        for signal in normalized:
            side = signal.side if signal.side in {"BUY", "SELL", "HOLD"} else "HOLD"
            reliability = 1.0 if signal.status in _READY_STATUSES else 0.4
            effective_weight = signal.weight * reliability * (signal.confidence / 100.0)
            score_buckets[side] += signal.score * effective_weight
            weight_buckets[side] += effective_weight
            readiness_total += reliability * signal.weight * 100.0
            readiness_weight += signal.weight
            if len(reasons) < 6:
                reasons.append(f"{signal.name}:{side}:{round(signal.score, 2)}")

        buy_score = score_buckets["BUY"] / weight_buckets["BUY"] if weight_buckets["BUY"] else 0.0
        sell_score = score_buckets["SELL"] / weight_buckets["SELL"] if weight_buckets["SELL"] else 0.0
        hold_score = score_buckets["HOLD"] / weight_buckets["HOLD"] if weight_buckets["HOLD"] else 50.0
        readiness = readiness_total / readiness_weight if readiness_weight else 0.0

        action = "HOLD"
        confidence = max(hold_score, 100.0 - abs(buy_score - sell_score)) if hold_score >= max(buy_score, sell_score) else 50.0
        if buy_score >= self.min_confidence and buy_score - sell_score >= self.decision_margin:
            action = "BUY"
            confidence = buy_score
        elif sell_score >= self.min_confidence and sell_score - buy_score >= self.decision_margin:
            action = "SELL"
            confidence = sell_score

        status = "READY" if readiness >= 60.0 else "LEARNING"
        if action == "HOLD":
            status = "OBSERVE" if status == "READY" else status

        return AdaptiveDecision(
            status=status,
            action=action,
            confidence=clamp(confidence),
            buy_score=clamp(buy_score),
            sell_score=clamp(sell_score),
            hold_score=clamp(hold_score),
            readiness=clamp(readiness),
            signal_count=len(normalized),
            reasons=reasons,
            diagnostics={"min_confidence": self.min_confidence, "decision_margin": self.decision_margin, "context": dict(context or {})},
        )
