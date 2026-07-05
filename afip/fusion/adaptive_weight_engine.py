"""Adaptive financial intelligence weight engine for AFIP Milestone B.

This module is additive and keeps backward compatibility with existing AFIP
runtime modules. It converts intelligence evidence into normalized allocation
weights that can be consumed by the Milestone B fusion runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class AdaptiveWeightResult:
    """Normalized intelligence allocation result."""

    status: str
    weights: dict[str, float]
    dominant_category: str
    concentration: float
    reason: str


class AdaptiveWeightEngine:
    """Build normalized adaptive allocation weights from intelligence inputs."""

    minimum_weight: float = 0.03

    def calculate(self, intelligence_inputs: Iterable[Mapping[str, object]]) -> AdaptiveWeightResult:
        raw_scores: dict[str, float] = {}
        for item in intelligence_inputs:
            category = str(item.get("category", "UNCLASSIFIED")).upper()
            confidence = _to_unit_float(item.get("confidence", 0.0))
            performance = _to_unit_float(item.get("performance", 0.5))
            reliability = _to_unit_float(item.get("reliability", 0.5))
            activity = _to_unit_float(item.get("activity", 1.0))
            contribution = confidence * (0.50 + performance * 0.30 + reliability * 0.20) * activity
            raw_scores[category] = raw_scores.get(category, 0.0) + max(0.0, contribution)

        if not raw_scores or sum(raw_scores.values()) <= 0.0:
            return AdaptiveWeightResult(
                status="ADAPTIVE_WEIGHT_REVIEW",
                weights={},
                dominant_category="NONE",
                concentration=0.0,
                reason="insufficient_intelligence_contribution",
            )

        adjusted = {k: max(v, self.minimum_weight) for k, v in raw_scores.items()}
        total = sum(adjusted.values())
        weights = {k: round(v / total, 4) for k, v in adjusted.items()}
        dominant_category = max(weights, key=weights.get)
        concentration = round(max(weights.values()), 4)
        status = "ADAPTIVE_WEIGHT_READY" if concentration <= 0.70 else "ADAPTIVE_WEIGHT_REVIEW"
        reason = "balanced_adaptive_allocation" if status == "ADAPTIVE_WEIGHT_READY" else "allocation_concentration_review"
        return AdaptiveWeightResult(status, weights, dominant_category, concentration, reason)


def _to_unit_float(value: object) -> float:
    try:
        numeric = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0
    if numeric > 1.0:
        numeric = numeric / 100.0
    return min(1.0, max(0.0, numeric))
