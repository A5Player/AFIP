from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.fusion.intelligence_conflict_analyzer import IntelligenceConflictAnalyzer
from afip.fusion.intelligence_consensus_engine import IntelligenceConsensusEngine


@dataclass(frozen=True)
class ConflictPriorityResolutionResult:
    status: str
    resolution_action: str
    priority_direction: str
    priority_category: str
    priority_score: float
    reason: str


class ConflictPriorityResolver:
    """Resolve financial intelligence conflict by priority and consensus."""

    DEFAULT_PRIORITY = {
        "RISK": 1.35,
        "EXECUTION": 1.20,
        "LIQUIDITY": 1.10,
        "MARKET_STRUCTURE": 1.05,
        "TREND": 1.00,
        "MOMENTUM": 0.92,
        "VOLUME": 0.88,
        "SMC": 1.03,
    }

    def resolve(self, intelligence_inputs: Iterable[Mapping[str, object]] | None = None) -> ConflictPriorityResolutionResult:
        inputs = list(intelligence_inputs or [])
        analysis = IntelligenceConflictAnalyzer().analyze(inputs)
        consensus = IntelligenceConsensusEngine().evaluate(inputs)

        if not inputs:
            return ConflictPriorityResolutionResult(
                status="CONFLICT_PRIORITY_READY",
                resolution_action="WAIT",
                priority_direction="FLAT",
                priority_category="NONE",
                priority_score=0.0,
                reason="no_intelligence_priority_available",
            )

        category_scores: dict[str, float] = {}
        direction_scores = {"BUY": 0.0, "SELL": 0.0, "FLAT": 0.0}
        category_direction: dict[str, str] = {}
        for item in inputs:
            category = str(item.get("category", "GENERAL")).upper()
            direction = str(item.get("direction", "FLAT")).upper()
            if direction not in direction_scores:
                direction = "FLAT"
            confidence = self._normalize_float(item.get("confidence", 0.0))
            weight = self._normalize_weight(item.get("weight", 1.0))
            priority = self.DEFAULT_PRIORITY.get(category, 1.0)
            score = confidence * weight * priority
            category_scores[category] = category_scores.get(category, 0.0) + score
            direction_scores[direction] += score
            category_direction[category] = direction

        priority_category = max(category_scores, key=category_scores.get)
        priority_direction = max(direction_scores, key=direction_scores.get)
        total_score = sum(direction_scores.values()) or 1.0
        priority_score = direction_scores[priority_direction] / total_score

        if analysis.conflict_level == "HIGH" and consensus.consensus_level == "LOW":
            action = "WAIT"
            reason = "priority_reduced_by_high_conflict"
        elif priority_direction == "FLAT":
            action = "WAIT"
            reason = "priority_direction_flat"
        elif priority_score >= 0.58 or consensus.consensus_level == "HIGH":
            action = priority_direction
            reason = "priority_direction_accepted"
        else:
            action = "WAIT"
            reason = "priority_score_requires_review"

        return ConflictPriorityResolutionResult(
            status="CONFLICT_PRIORITY_READY",
            resolution_action=action,
            priority_direction=priority_direction,
            priority_category=priority_category,
            priority_score=round(priority_score, 4),
            reason=reason,
        )

    @staticmethod
    def _normalize_float(value: object) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        if number > 1.0:
            number = number / 100.0
        return max(0.0, min(number, 1.0))

    @staticmethod
    def _normalize_weight(value: object) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 1.0
        return max(0.0, number)
