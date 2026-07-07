"""Production readiness report contract."""

from __future__ import annotations

from dataclasses import dataclass

from .readiness_policy import ProductionReadinessDecision
from .readiness_profile import ProductionReadinessProfile


@dataclass(frozen=True)
class ProductionReadinessReport:
    """Serializable production readiness report."""

    decision: ProductionReadinessDecision
    profiles: tuple[ProductionReadinessProfile, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.decision.status,
            "ready": self.decision.status == "PRODUCTION_READY",
            "profile_count": len(self.profiles),
            "decision": self.decision.as_dict(),
            "profiles": [item.as_dict() for item in self.profiles],
            "architecture": {
                "market_regime_before_signal_context": True,
                "data_first_architecture": True,
                "knowledge_first_architecture": True,
                "deterministic_runtime": True,
                "validation_before_production_readiness": True,
                "production_gate_before_live_execution": True,
                "live_execution_allowed": False,
            },
        }
