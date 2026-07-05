from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.fusion.confidence_reconciliation import ConfidenceReconciliation
from afip.fusion.conflict_priority_resolver import ConflictPriorityResolver
from afip.fusion.intelligence_conflict_analyzer import IntelligenceConflictAnalyzer
from afip.fusion.intelligence_consensus_engine import IntelligenceConsensusEngine


@dataclass(frozen=True)
class ProductionMilestoneBConflictRuntimeResult:
    status: str
    action: str
    confidence: float
    conflict_level: str
    consensus_level: str
    priority_category: str
    decision_quality: str
    reason: str


class ProductionMilestoneBConflictRuntime:
    """Production runtime layer for intelligence conflict resolution."""

    def run(self, intelligence_inputs: Iterable[Mapping[str, object]] | None = None) -> ProductionMilestoneBConflictRuntimeResult:
        inputs = list(intelligence_inputs or self._default_inputs())
        analysis = IntelligenceConflictAnalyzer().analyze(inputs)
        consensus = IntelligenceConsensusEngine().evaluate(inputs)
        resolution = ConflictPriorityResolver().resolve(inputs)
        reconciliation = ConfidenceReconciliation().reconcile(inputs)

        return ProductionMilestoneBConflictRuntimeResult(
            status="MILESTONE_B_CONFLICT_RUNTIME_READY",
            action=reconciliation.reconciled_direction if reconciliation.reconciled_direction != "FLAT" else resolution.resolution_action,
            confidence=reconciliation.reconciled_confidence,
            conflict_level=analysis.conflict_level,
            consensus_level=consensus.consensus_level,
            priority_category=resolution.priority_category,
            decision_quality=reconciliation.decision_quality,
            reason=reconciliation.reason,
        )

    @staticmethod
    def _default_inputs() -> list[dict[str, object]]:
        return [
            {"category": "TREND", "direction": "BUY", "confidence": 0.84, "weight": 0.28},
            {"category": "LIQUIDITY", "direction": "BUY", "confidence": 0.78, "weight": 0.24},
            {"category": "EXECUTION", "direction": "BUY", "confidence": 0.74, "weight": 0.18},
            {"category": "RISK", "direction": "FLAT", "confidence": 0.30, "weight": 0.10},
        ]
