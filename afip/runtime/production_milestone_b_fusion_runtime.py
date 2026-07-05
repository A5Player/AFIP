"""Production Milestone B fusion runtime for AFIP Pack B1.1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.fusion.intelligence_fusion_core import IntelligenceFusionCore


@dataclass(frozen=True)
class ProductionMilestoneBFusionRuntimeResult:
    """Milestone B fusion runtime result."""

    status: str
    action: str
    direction: str
    confidence: float
    execution_mode: str
    reason: str


class ProductionMilestoneBFusionRuntime:
    """Evaluate unified financial intelligence for Milestone B without live execution."""

    def __init__(self) -> None:
        """Create an additive runtime that preserves simulation-only behavior."""
        self._fusion_core = IntelligenceFusionCore()

    def evaluate(
        self,
        signals: Iterable[Mapping[str, float | str]],
        priority_metrics: Mapping[str, float],
    ) -> ProductionMilestoneBFusionRuntimeResult:
        """Return fusion runtime output with locked simulation execution mode."""
        fusion = self._fusion_core.evaluate(signals=signals, priority_metrics=priority_metrics)

        if fusion.status == "UNIFIED_INTELLIGENCE_READY":
            status = "MILESTONE_B_FUSION_READY"
            action = "PREPARE_SIMULATION_ORDER_REVIEW"
            execution_mode = "LOCKED_SIMULATION_ONLY"
            reason = "unified_financial_intelligence_ready"
        elif fusion.status == "UNIFIED_INTELLIGENCE_REVIEW":
            status = "MILESTONE_B_FUSION_REVIEW"
            action = "CONTINUE_FUSION_REVIEW"
            execution_mode = "LOCKED_SIMULATION_ONLY"
            reason = "unified_financial_intelligence_requires_review"
        else:
            status = "MILESTONE_B_FUSION_NOT_READY"
            action = "KEEP_SIMULATION_ONLY"
            execution_mode = "LOCKED_SIMULATION_ONLY"
            reason = "unified_financial_intelligence_not_ready"

        return ProductionMilestoneBFusionRuntimeResult(
            status=status,
            action=action,
            direction=fusion.direction,
            confidence=fusion.confidence,
            execution_mode=execution_mode,
            reason=reason,
        )
