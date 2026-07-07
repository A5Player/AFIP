"""Adaptive confidence report model."""

from __future__ import annotations

from dataclasses import dataclass

from .confidence_policy import AdaptiveConfidenceDecision
from .confidence_profile import AdaptiveConfidenceProfile


@dataclass(frozen=True)
class AdaptiveConfidenceReport:
    """Serializable adaptive confidence report."""

    decision: AdaptiveConfidenceDecision
    profiles: tuple[AdaptiveConfidenceProfile, ...]

    @property
    def ready(self) -> bool:
        return self.decision.readiness == "READY"

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.decision.status,
            "ready": self.ready,
            "decision": self.decision.as_dict(),
            "profile_count": len(self.profiles),
            "profiles": [item.as_dict() for item in self.profiles],
            "architecture": {
                "market_regime_before_signal_context": True,
                "data_first": True,
                "knowledge_first": True,
                "deterministic_runtime": True,
                "production_learning_write": False,
                "confidence_runtime_write": False,
            },
        }
