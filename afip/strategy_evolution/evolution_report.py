"""Strategy evolution report contract."""

from __future__ import annotations

from dataclasses import dataclass

from .evolution_policy import StrategyEvolutionDecision
from .evolution_profile import StrategyEvolutionProfile


@dataclass(frozen=True)
class StrategyEvolutionReport:
    """Serializable strategy evolution runtime report."""

    decision: StrategyEvolutionDecision
    profiles: tuple[StrategyEvolutionProfile, ...]

    @property
    def ready(self) -> bool:
        return self.decision.status == "STRATEGY_EVOLUTION_READY"

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
                "strategy_runtime_write": self.decision.runtime_write,
                "deterministic_runtime": True,
                "financial_terminology_only": True,
            },
        }
