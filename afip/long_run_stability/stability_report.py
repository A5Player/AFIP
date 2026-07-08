"""Long-run stability report for Production Milestone G Pack 7."""

from __future__ import annotations

from dataclasses import dataclass

from .stability_profile import LongRunStabilityProfile


@dataclass(frozen=True)
class LongRunStabilityReport:
    """Human-readable stability report for production review."""

    profile: LongRunStabilityProfile

    def as_text(self) -> str:
        lines = [
            "Long-run Stability Report",
            f"Market regime: {self.profile.market_regime}",
            f"Signal context: {self.profile.signal_context}",
            f"Execution mode: {self.profile.execution_mode}",
            f"Configuration version: {self.profile.configuration_version}",
            f"Repeated runs: {self.profile.repeated_runs}",
            f"Deterministic consistency: {self.profile.deterministic_consistency:.4f}",
            f"Stability quality: {self.profile.stability_quality:.4f}",
            f"Long-run score: {self.profile.long_run_score:.4f}",
            f"Readiness gate: {self.profile.readiness_gate}",
            f"Decision reason: {self.profile.reason}",
        ]
        return "\n".join(lines)
