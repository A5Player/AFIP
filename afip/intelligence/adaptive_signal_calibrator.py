"""Production Milestone A Pack 2: adaptive signal calibration.

The module is additive and dependency-free. It converts recent financial
performance observations into conservative score and confidence adjustments
without changing existing public contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping

from afip.intelligence.adaptive_intelligence_core import AdaptiveSignal, clamp


@dataclass(frozen=True)
class SignalCalibrationProfile:
    """Calibration result for one financial intelligence signal group."""

    group: str
    sample_count: int
    win_rate: float
    average_return_points: float
    score_adjustment: float
    confidence_adjustment: float
    status: str = "READY"
    reason: str = "signal_calibration_ready"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group": self.group,
            "sample_count": self.sample_count,
            "win_rate": round(self.win_rate, 2),
            "average_return_points": round(self.average_return_points, 2),
            "score_adjustment": round(self.score_adjustment, 2),
            "confidence_adjustment": round(self.confidence_adjustment, 2),
            "status": self.status,
            "reason": self.reason,
        }


class AdaptiveSignalCalibrator:
    """Calibrates adaptive signals from recent outcome samples."""

    def __init__(self, minimum_samples: int = 5, maximum_adjustment: float = 6.0) -> None:
        self.minimum_samples = max(1, int(minimum_samples))
        self.maximum_adjustment = max(0.0, float(maximum_adjustment))

    def build_profile(self, group: str, samples: Iterable[Mapping[str, Any]]) -> SignalCalibrationProfile:
        selected = [s for s in samples if str(s.get("group", group)) == group]
        if len(selected) < self.minimum_samples:
            return SignalCalibrationProfile(
                group=group,
                sample_count=len(selected),
                win_rate=0.0,
                average_return_points=0.0,
                score_adjustment=0.0,
                confidence_adjustment=-2.0,
                status="LEARNING",
                reason="insufficient_calibration_samples",
            )

        wins = sum(1 for item in selected if str(item.get("outcome", "")).upper() == "WIN")
        returns = [float(item.get("net_points", 0.0) or 0.0) for item in selected]
        win_rate = wins / len(selected) * 100.0
        average_return = sum(returns) / len(returns)

        performance_edge = (win_rate - 50.0) / 10.0 + average_return / 250.0
        score_adjustment = clamp(performance_edge, -self.maximum_adjustment, self.maximum_adjustment)
        confidence_adjustment = clamp(performance_edge * 0.75, -self.maximum_adjustment, self.maximum_adjustment)
        reason = "positive_calibration_edge" if score_adjustment > 0 else "defensive_calibration_edge"

        return SignalCalibrationProfile(
            group=group,
            sample_count=len(selected),
            win_rate=win_rate,
            average_return_points=average_return,
            score_adjustment=score_adjustment,
            confidence_adjustment=confidence_adjustment,
            reason=reason,
        )

    def calibrate_signal(self, signal: AdaptiveSignal | Mapping[str, Any], profile: SignalCalibrationProfile) -> AdaptiveSignal:
        normalized = signal if isinstance(signal, AdaptiveSignal) else AdaptiveSignal.from_mapping(signal)
        if normalized.group != profile.group or profile.status != "READY":
            return normalized
        return AdaptiveSignal(
            name=normalized.name,
            group=normalized.group,
            side=normalized.side,
            score=clamp(normalized.score + profile.score_adjustment),
            confidence=clamp(normalized.confidence + profile.confidence_adjustment),
            weight=normalized.weight,
            status=normalized.status,
            reason=f"{normalized.reason}|{profile.reason}",
            metadata={**normalized.metadata, "calibration_profile": profile.to_dict()},
        )
