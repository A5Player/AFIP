"""Runtime adaptation report contract."""

from __future__ import annotations

from dataclasses import dataclass

from .adaptation_policy import RuntimeAdaptationDecision
from .adaptation_profile import RuntimeAdaptationProfile


@dataclass(frozen=True)
class RuntimeAdaptationReport:
    """Serializable runtime adaptation report."""

    decision: RuntimeAdaptationDecision
    profiles: tuple[RuntimeAdaptationProfile, ...]

    @property
    def ready(self) -> bool:
        return self.decision.status == "RUNTIME_ADAPTATION_READY"

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.decision.status,
            "ready": self.ready,
            "profile_count": len(self.profiles),
            "decision": self.decision.as_dict(),
            "profiles": [item.as_dict() for item in self.profiles],
            "architecture": {
                "market_regime_before_signal_context": True,
                "data_first_architecture": True,
                "knowledge_first_architecture": True,
                "strategy_evolution_required": True,
                "runtime_plan_write": self.decision.runtime_write,
                "deterministic_runtime": True,
                "financial_terminology_only": True,
            },
        }
