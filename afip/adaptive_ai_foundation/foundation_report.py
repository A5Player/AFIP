"""Adaptive AI foundation report model."""

from __future__ import annotations

from dataclasses import dataclass

from .foundation_policy import AdaptiveAIFoundationDecision
from .foundation_profile import AdaptiveAIFoundationProfile


@dataclass(frozen=True)
class AdaptiveAIFoundationReport:
    """Serializable adaptive AI foundation report."""

    decision: AdaptiveAIFoundationDecision
    profiles: tuple[AdaptiveAIFoundationProfile, ...]

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
                "market_regime_before_signal": True,
                "data_first": True,
                "knowledge_first": True,
                "deterministic_runtime": True,
            },
        }
