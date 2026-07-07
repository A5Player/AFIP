"""Milestone F completion report contract."""

from __future__ import annotations

from dataclasses import dataclass

from .final_policy import MilestoneFCompletionDecision
from .final_profile import MilestoneFCompletionProfile


@dataclass(frozen=True)
class MilestoneFCompletionReport:
    """Serializable Milestone F completion report."""

    decision: MilestoneFCompletionDecision
    profiles: tuple[MilestoneFCompletionProfile, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.decision.status,
            "complete": self.decision.status == "MILESTONE_F_COMPLETE",
            "profile_count": len(self.profiles),
            "decision": self.decision.as_dict(),
            "profiles": [item.as_dict() for item in self.profiles],
            "architecture": {
                "market_regime_before_signal_context": True,
                "data_first_architecture": True,
                "knowledge_first_architecture": True,
                "deterministic_runtime": True,
                "production_readiness_before_milestone_completion": True,
                "handoff_required_before_next_milestone": True,
                "live_execution_allowed": False,
            },
        }
