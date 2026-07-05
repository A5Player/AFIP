"""Production intelligence fusion core for AFIP Milestone B Pack 1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.fusion.intelligence_conflict_resolution import IntelligenceConflictResolution
from afip.fusion.intelligence_priority_matrix import IntelligencePriorityMatrix
from afip.fusion.intelligence_score_fusion import IntelligenceScoreFusion


@dataclass(frozen=True)
class IntelligenceFusionCoreResult:
    """Unified financial intelligence fusion result."""

    status: str
    action: str
    direction: str
    confidence: float
    priority_score: float
    conflict_score: float
    reason: str


class IntelligenceFusionCore:
    """Combine score fusion, priority allocation, and conflict resolution."""

    def __init__(self) -> None:
        """Create deterministic additive fusion dependencies."""
        self._score_fusion = IntelligenceScoreFusion()
        self._priority_matrix = IntelligencePriorityMatrix()
        self._conflict_resolution = IntelligenceConflictResolution()

    def evaluate(
        self,
        signals: Iterable[Mapping[str, float | str]],
        priority_metrics: Mapping[str, float],
    ) -> IntelligenceFusionCoreResult:
        """Return a unified financial intelligence decision without execution side effects."""
        signal_list = list(signals)
        score_result = self._score_fusion.fuse(signal_list)
        priority_result = self._priority_matrix.evaluate(priority_metrics)
        conflict_result = self._conflict_resolution.resolve(signal_list)

        confidence = round(
            score_result.confidence * 0.55
            + priority_result.priority_score * 0.30
            + max(0.0, 100.0 - conflict_result.conflict_score) * 0.15,
            2,
        )

        if (
            score_result.status == "FUSION_SCORE_READY"
            and priority_result.status == "PRIORITY_MATRIX_READY"
            and conflict_result.status == "CONFLICT_RESOLVED"
            and confidence >= 74.0
        ):
            status = "UNIFIED_INTELLIGENCE_READY"
            action = "ACCEPT_UNIFIED_FINANCIAL_DIRECTION"
            direction = conflict_result.resolved_direction
            reason = "score_priority_and_conflict_inputs_aligned"
        elif confidence >= 58.0:
            status = "UNIFIED_INTELLIGENCE_REVIEW"
            action = "REVIEW_UNIFIED_FINANCIAL_DIRECTION"
            direction = "FLAT"
            reason = "unified_financial_inputs_require_review"
        else:
            status = "UNIFIED_INTELLIGENCE_NOT_READY"
            action = "KEEP_SIMULATION_ONLY"
            direction = "FLAT"
            reason = "unified_financial_inputs_below_threshold"

        return IntelligenceFusionCoreResult(
            status=status,
            action=action,
            direction=direction,
            confidence=confidence,
            priority_score=priority_result.priority_score,
            conflict_score=conflict_result.conflict_score,
            reason=reason,
        )
