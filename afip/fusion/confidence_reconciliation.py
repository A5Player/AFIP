from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.fusion.conflict_priority_resolver import ConflictPriorityResolver
from afip.fusion.intelligence_conflict_analyzer import IntelligenceConflictAnalyzer
from afip.fusion.intelligence_consensus_engine import IntelligenceConsensusEngine


@dataclass(frozen=True)
class ConfidenceReconciliationResult:
    status: str
    reconciled_direction: str
    reconciled_confidence: float
    decision_quality: str
    reason: str


class ConfidenceReconciliation:
    """Reconcile confidence after conflict, consensus, and priority evaluation."""

    def reconcile(self, intelligence_inputs: Iterable[Mapping[str, object]] | None = None) -> ConfidenceReconciliationResult:
        inputs = list(intelligence_inputs or [])
        analysis = IntelligenceConflictAnalyzer().analyze(inputs)
        consensus = IntelligenceConsensusEngine().evaluate(inputs)
        resolution = ConflictPriorityResolver().resolve(inputs)

        if not inputs:
            return ConfidenceReconciliationResult(
                status="CONFIDENCE_RECONCILIATION_READY",
                reconciled_direction="FLAT",
                reconciled_confidence=0.0,
                decision_quality="INSUFFICIENT",
                reason="no_confidence_to_reconcile",
            )

        if resolution.resolution_action == "WAIT":
            base_confidence = consensus.consensus_score * (1.0 - analysis.conflict_ratio)
            direction = "FLAT"
        else:
            base_confidence = (consensus.consensus_score * 0.55) + (resolution.priority_score * 0.45)
            if analysis.conflict_level == "HIGH":
                base_confidence *= 0.78
            elif analysis.conflict_level == "MODERATE":
                base_confidence *= 0.90
            direction = resolution.resolution_action

        confidence = round(max(0.0, min(base_confidence, 1.0)), 4)
        quality = self._quality(confidence, resolution.resolution_action)
        reason = self._reason(quality, analysis.conflict_level)

        return ConfidenceReconciliationResult(
            status="CONFIDENCE_RECONCILIATION_READY",
            reconciled_direction=direction,
            reconciled_confidence=confidence,
            decision_quality=quality,
            reason=reason,
        )

    @staticmethod
    def _quality(confidence: float, action: str) -> str:
        if action == "WAIT":
            return "REVIEW"
        if confidence >= 0.72:
            return "HIGH"
        if confidence >= 0.52:
            return "MODERATE"
        return "REVIEW"

    @staticmethod
    def _reason(quality: str, conflict_level: str) -> str:
        if quality == "REVIEW":
            return "confidence_requires_review"
        if conflict_level == "LOW":
            return "confidence_supported_by_alignment"
        return "confidence_adjusted_for_conflict"
