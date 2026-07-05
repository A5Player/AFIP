"""Production Milestone A Pack 3: adaptive weight allocation.

This additive module adjusts financial intelligence weights from objective
quality factors while preserving existing signal contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping

from afip.intelligence.adaptive_intelligence_core import AdaptiveSignal, clamp


@dataclass(frozen=True)
class WeightAllocationProfile:
    """Weight allocation profile for one financial intelligence group."""

    group: str
    base_weight: float
    quality_score: float
    allocated_weight: float
    status: str = "READY"
    reason: str = "weight_allocation_ready"
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group": self.group,
            "base_weight": round(self.base_weight, 4),
            "quality_score": round(self.quality_score, 2),
            "allocated_weight": round(self.allocated_weight, 4),
            "status": self.status,
            "reason": self.reason,
            "diagnostics": dict(self.diagnostics),
        }


class AdaptiveWeightAllocator:
    """Allocates conservative production weights to adaptive signals."""

    def __init__(self, minimum_weight: float = 0.25, maximum_weight: float = 2.0) -> None:
        self.minimum_weight = max(0.0, float(minimum_weight))
        self.maximum_weight = max(self.minimum_weight, float(maximum_weight))

    def build_profile(self, group: str, quality_factors: Mapping[str, Any]) -> WeightAllocationProfile:
        base_weight = max(0.0, float(quality_factors.get("base_weight", 1.0) or 1.0))
        win_rate = clamp(float(quality_factors.get("win_rate", 50.0) or 50.0))
        stability = clamp(float(quality_factors.get("stability", 50.0) or 50.0))
        drawdown_control = clamp(float(quality_factors.get("drawdown_control", 50.0) or 50.0))
        sample_quality = clamp(float(quality_factors.get("sample_quality", 50.0) or 50.0))

        quality_score = win_rate * 0.35 + stability * 0.25 + drawdown_control * 0.25 + sample_quality * 0.15
        multiplier = 0.75 + (quality_score - 50.0) / 100.0
        allocated_weight = min(self.maximum_weight, max(self.minimum_weight, base_weight * multiplier))
        status = "READY" if sample_quality >= 40.0 else "LEARNING"
        reason = "quality_weight_allocated" if status == "READY" else "sample_quality_learning"

        return WeightAllocationProfile(
            group=group,
            base_weight=base_weight,
            quality_score=quality_score,
            allocated_weight=allocated_weight,
            status=status,
            reason=reason,
            diagnostics={
                "win_rate": win_rate,
                "stability": stability,
                "drawdown_control": drawdown_control,
                "sample_quality": sample_quality,
            },
        )

    def allocate(self, signals: Iterable[AdaptiveSignal | Mapping[str, Any]], profiles: Mapping[str, WeightAllocationProfile]) -> list[AdaptiveSignal]:
        allocated: list[AdaptiveSignal] = []
        for signal in signals:
            normalized = signal if isinstance(signal, AdaptiveSignal) else AdaptiveSignal.from_mapping(signal)
            profile = profiles.get(normalized.group)
            if profile is None or profile.status != "READY":
                allocated.append(normalized)
                continue
            allocated.append(
                AdaptiveSignal(
                    name=normalized.name,
                    group=normalized.group,
                    side=normalized.side,
                    score=normalized.score,
                    confidence=normalized.confidence,
                    weight=profile.allocated_weight,
                    status=normalized.status,
                    reason=f"{normalized.reason}|{profile.reason}",
                    metadata={**normalized.metadata, "weight_allocation": profile.to_dict()},
                )
            )
        return allocated
