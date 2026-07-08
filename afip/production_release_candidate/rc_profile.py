"""Production release candidate profile for Production Milestone G Pack 8."""

from __future__ import annotations

from dataclasses import dataclass

from .rc_observation import ProductionReleaseCandidateObservation


@dataclass(frozen=True)
class ProductionReleaseCandidateProfile:
    """Deterministic profile summarizing RC readiness."""

    market_regime: str
    signal_context: str
    execution_mode: str
    configuration_version: str
    long_run_score: float
    production_hardening_score: float
    paper_trading_score: float
    observability_score: float
    feature_flag_score: float
    event_log_score: float
    deployment_checklist_score: float
    release_notes_score: float
    rollback_plan_score: float
    operator_handoff_score: float
    unresolved_reviews: int
    release_evidence_quality: float
    production_release_score: float
    status: str
    review_required: bool
    reason: str

    @classmethod
    def from_observation(
        cls,
        observation: ProductionReleaseCandidateObservation,
        status: str,
        reason: str,
    ) -> "ProductionReleaseCandidateProfile":
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            execution_mode=observation.execution_mode,
            configuration_version=observation.configuration_version,
            long_run_score=round(observation.long_run_score, 4),
            production_hardening_score=round(observation.production_hardening_score, 4),
            paper_trading_score=round(observation.paper_trading_score, 4),
            observability_score=round(observation.observability_score, 4),
            feature_flag_score=round(observation.feature_flag_score, 4),
            event_log_score=round(observation.event_log_score, 4),
            deployment_checklist_score=round(observation.deployment_checklist_score, 4),
            release_notes_score=round(observation.release_notes_score, 4),
            rollback_plan_score=round(observation.rollback_plan_score, 4),
            operator_handoff_score=round(observation.operator_handoff_score, 4),
            unresolved_reviews=observation.unresolved_reviews,
            release_evidence_quality=round(observation.release_evidence_quality, 4),
            production_release_score=round(observation.production_release_score, 4),
            status=status,
            review_required=status != "READY",
            reason=reason,
        )

    @property
    def readiness_gate(self) -> str:
        if self.status == "BLOCKED":
            return "BLOCKED"
        if self.status == "REVIEW":
            return "REVIEW_REQUIRED"
        return "PRODUCTION_RELEASE_CANDIDATE_READY"
