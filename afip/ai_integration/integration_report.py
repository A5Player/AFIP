"""AI integration report."""

from __future__ import annotations

from dataclasses import dataclass

from .integration_policy import AIIntegrationDecision
from .integration_profile import AIIntegrationProfile


@dataclass(frozen=True)
class AIIntegrationReport:
    """Serializable AI integration report."""

    decision: AIIntegrationDecision
    profiles: tuple[AIIntegrationProfile, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.decision.status,
            "ready": self.decision.readiness == "READY",
            "profile_count": len(self.profiles),
            "decision": self.decision.as_dict(),
            "profiles": [item.as_dict() for item in self.profiles],
            "architecture": {
                "market_regime_before_signal_context": True,
                "data_first_architecture": True,
                "knowledge_first_architecture": True,
                "deterministic_runtime": True,
                "autonomous_execution": False,
                "ai_output_write": False,
                "financial_terminology_only": True,
            },
        }
