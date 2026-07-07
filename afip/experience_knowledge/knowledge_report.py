"""Experience knowledge report model."""

from __future__ import annotations

from dataclasses import dataclass

from .knowledge_policy import ExperienceKnowledgeDecision
from .knowledge_profile import ExperienceKnowledgeProfile


@dataclass(frozen=True)
class ExperienceKnowledgeReport:
    """Serializable experience knowledge report."""

    decision: ExperienceKnowledgeDecision
    profiles: tuple[ExperienceKnowledgeProfile, ...]

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
                "experience_runtime_write": False,
                "production_learning_write": False,
            },
        }
