"""Paper trading report for Production Milestone G Pack 6."""

from __future__ import annotations

from dataclasses import dataclass

from .paper_profile import PaperTradingProfile


@dataclass(frozen=True)
class PaperTradingReport:
    """Human-readable paper trading readiness report."""

    profile: PaperTradingProfile

    def as_text(self) -> str:
        lines = [
            "Paper Trading Report",
            f"Market regime: {self.profile.market_regime}",
            f"Signal context: {self.profile.signal_context}",
            f"Execution mode: {self.profile.execution_mode}",
            f"Configuration version: {self.profile.configuration_version}",
            f"Decision action: {self.profile.decision_action}",
            f"Paper quality: {self.profile.paper_quality:.4f}",
            f"Continuity score: {self.profile.continuity_score:.4f}",
            f"Readiness gate: {self.profile.readiness_gate}",
            f"Decision reason: {self.profile.reason}",
        ]
        return "\n".join(lines)
