from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.decision.unified_decision_engine import UnifiedDecisionEngine


@dataclass(frozen=True)
class ProductionMilestoneBDecisionRuntimeResult:
    status: str
    action: str
    confidence: float
    confidence_level: str
    risk_status: str
    execution_status: str
    reason: str


class ProductionMilestoneBDecisionRuntime:
    """Production runtime layer for unified Milestone B decisions."""

    def run(
        self,
        fusion_profile: Mapping[str, object] | None = None,
        weight_profile: Mapping[str, object] | None = None,
        conflict_profile: Mapping[str, object] | None = None,
        risk_profile: Mapping[str, object] | None = None,
        supporting_factors: Iterable[str] | None = None,
    ) -> ProductionMilestoneBDecisionRuntimeResult:
        decision = UnifiedDecisionEngine().decide(
            fusion_profile=fusion_profile or self._default_fusion(),
            weight_profile=weight_profile or self._default_weight(),
            conflict_profile=conflict_profile or self._default_conflict(),
            risk_profile=risk_profile or self._default_risk(),
            supporting_factors=supporting_factors or ("trend", "liquidity", "execution"),
        )
        return ProductionMilestoneBDecisionRuntimeResult(
            status="MILESTONE_B_DECISION_RUNTIME_READY",
            action=decision.action,
            confidence=decision.confidence,
            confidence_level=decision.confidence_level,
            risk_status=decision.risk_status,
            execution_status=decision.execution_status,
            reason=decision.reason,
        )

    @staticmethod
    def _default_fusion() -> dict[str, object]:
        return {"direction": "BUY", "confidence": 0.86, "score": 0.86}

    @staticmethod
    def _default_weight() -> dict[str, object]:
        return {"adaptive_score": 0.84, "status": "ADAPTIVE_WEIGHT_READY"}

    @staticmethod
    def _default_conflict() -> dict[str, object]:
        return {"reconciled_direction": "BUY", "consensus_level": "HIGH", "consensus_score": 0.83, "conflict_ratio": 0.10}

    @staticmethod
    def _default_risk() -> dict[str, object]:
        return {"risk_accepted": True, "execution_quality": "ACCEPTABLE"}
