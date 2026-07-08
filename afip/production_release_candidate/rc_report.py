"""Production release candidate report for Production Milestone G Pack 8."""

from __future__ import annotations

from dataclasses import dataclass

from .rc_profile import ProductionReleaseCandidateProfile


@dataclass(frozen=True)
class ProductionReleaseCandidateReport:
    """Human-readable RC report for production review."""

    profile: ProductionReleaseCandidateProfile

    def as_text(self) -> str:
        lines = [
            "Production Release Candidate Report",
            f"Market regime: {self.profile.market_regime}",
            f"Signal context: {self.profile.signal_context}",
            f"Execution mode: {self.profile.execution_mode}",
            f"Configuration version: {self.profile.configuration_version}",
            f"Long-run score: {self.profile.long_run_score:.4f}",
            f"Deployment checklist score: {self.profile.deployment_checklist_score:.4f}",
            f"Release evidence quality: {self.profile.release_evidence_quality:.4f}",
            f"Production release score: {self.profile.production_release_score:.4f}",
            f"Unresolved reviews: {self.profile.unresolved_reviews}",
            f"Readiness gate: {self.profile.readiness_gate}",
            f"Decision reason: {self.profile.reason}",
        ]
        return "\n".join(lines)
