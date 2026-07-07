"""Self evaluation report model."""

from __future__ import annotations

from dataclasses import dataclass

from .evaluation_policy import SelfEvaluationDecision
from .evaluation_profile import SelfEvaluationProfile


@dataclass(frozen=True)
class SelfEvaluationReport:
    """Serializable self evaluation report."""

    decision: SelfEvaluationDecision
    profiles: tuple[SelfEvaluationProfile, ...]

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
                "market_regime_before_outcome_review": True,
                "data_first": True,
                "knowledge_first": True,
                "deterministic_runtime": True,
                "production_learning_write": False,
            },
        }
