"""Production Milestone A Pack 4: adaptive signal quality auditor.

This module is additive and keeps the existing AFIP intelligence contract intact.
It uses international financial terminology only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping

from afip.intelligence.adaptive_intelligence_core import AdaptiveSignal


@dataclass(frozen=True)
class SignalQualityAuditResult:
    """Quality audit for a group of adaptive market signals."""

    status: str
    quality_score: float
    accepted_signals: int
    rejected_signals: int
    dominant_side: str
    side_consistency: float
    blockers: list[str] = field(default_factory=list)
    reason: str = "signal_quality_audit_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "quality_score": round(self.quality_score, 2),
            "accepted_signals": self.accepted_signals,
            "rejected_signals": self.rejected_signals,
            "dominant_side": self.dominant_side,
            "side_consistency": round(self.side_consistency, 2),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class SignalQualityAuditor:
    """Validates signal quality before adaptive runtime decisions are used."""

    VALID_SIDES = {"BUY", "SELL", "FLAT", "HOLD"}

    def __init__(self, minimum_score: float = 55.0, minimum_confidence: float = 55.0, minimum_consistency: float = 60.0) -> None:
        self.minimum_score = float(minimum_score)
        self.minimum_confidence = float(minimum_confidence)
        self.minimum_consistency = float(minimum_consistency)

    def audit(self, signals: Iterable[AdaptiveSignal | Mapping[str, Any]]) -> SignalQualityAuditResult:
        parsed = [s if isinstance(s, AdaptiveSignal) else AdaptiveSignal.from_mapping(s) for s in signals]
        if not parsed:
            return SignalQualityAuditResult(
                status="OBSERVE",
                quality_score=0.0,
                accepted_signals=0,
                rejected_signals=0,
                dominant_side="HOLD",
                side_consistency=0.0,
                blockers=["no_adaptive_signals"],
                reason="signal_quality_audit_waiting_for_signals",
            )

        accepted: list[AdaptiveSignal] = []
        rejected = 0
        side_counts: Dict[str, int] = {}
        quality_values: list[float] = []

        for signal in parsed:
            side = str(signal.side).upper()
            valid_side = side in self.VALID_SIDES
            quality = (float(signal.score) * 0.55) + (float(signal.confidence) * 0.35) + (float(signal.weight) * 10.0)
            quality = max(0.0, min(100.0, quality))
            quality_values.append(quality)
            if valid_side and signal.score >= self.minimum_score and signal.confidence >= self.minimum_confidence:
                accepted.append(signal)
                side_counts[side] = side_counts.get(side, 0) + 1
            else:
                rejected += 1

        dominant_side = max(side_counts, key=side_counts.get) if side_counts else "HOLD"
        side_consistency = (side_counts.get(dominant_side, 0) / len(accepted) * 100.0) if accepted else 0.0
        quality_score = sum(quality_values) / len(quality_values)

        blockers: list[str] = []
        if not accepted:
            blockers.append("no_qualified_adaptive_signals")
        if side_consistency < self.minimum_consistency:
            blockers.append("low_signal_side_consistency")
        if quality_score < self.minimum_score:
            blockers.append("low_signal_quality_score")

        return SignalQualityAuditResult(
            status="READY" if not blockers else "OBSERVE",
            quality_score=quality_score,
            accepted_signals=len(accepted),
            rejected_signals=rejected,
            dominant_side=dominant_side,
            side_consistency=side_consistency,
            blockers=blockers,
            reason="signal_quality_audit_ready" if not blockers else "signal_quality_audit_protective_observation",
        )
