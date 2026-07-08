"""Production release candidate policy for deterministic production review."""

from __future__ import annotations

from dataclasses import dataclass

from .rc_observation import ProductionReleaseCandidateObservation


@dataclass(frozen=True)
class ProductionReleaseCandidatePolicy:
    """Deterministic gate for Release Candidate evidence."""

    minimum_long_run_score: float = 0.78
    minimum_hardening_score: float = 0.76
    minimum_paper_trading_score: float = 0.72
    minimum_observability_score: float = 0.72
    minimum_feature_flag_score: float = 0.70
    minimum_event_log_score: float = 0.70
    minimum_deployment_checklist_score: float = 0.82
    minimum_release_notes_score: float = 0.72
    minimum_rollback_plan_score: float = 0.74
    minimum_operator_handoff_score: float = 0.74
    minimum_release_evidence_quality: float = 0.78
    minimum_production_release_score: float = 0.80

    def evaluate_reason(self, observation: ProductionReleaseCandidateObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.simulation_only:
            return "live_execution_not_allowed_for_release_candidate"
        if observation.unresolved_reviews > 0:
            return "unresolved_review_required"
        if observation.long_run_score < self.minimum_long_run_score:
            return "long_run_stability_review_required"
        if observation.production_hardening_score < self.minimum_hardening_score:
            return "production_hardening_review_required"
        if observation.paper_trading_score < self.minimum_paper_trading_score:
            return "paper_trading_review_required"
        if observation.observability_score < self.minimum_observability_score:
            return "observability_review_required"
        if observation.feature_flag_score < self.minimum_feature_flag_score:
            return "feature_flag_review_required"
        if observation.event_log_score < self.minimum_event_log_score:
            return "event_log_review_required"
        if observation.deployment_checklist_score < self.minimum_deployment_checklist_score:
            return "deployment_checklist_review_required"
        if observation.release_notes_score < self.minimum_release_notes_score:
            return "release_notes_review_required"
        if observation.rollback_plan_score < self.minimum_rollback_plan_score:
            return "rollback_plan_review_required"
        if observation.operator_handoff_score < self.minimum_operator_handoff_score:
            return "operator_handoff_review_required"
        if observation.release_evidence_quality < self.minimum_release_evidence_quality:
            return "release_evidence_quality_review_required"
        if observation.production_release_score < self.minimum_production_release_score:
            return "production_release_score_review_required"
        return "production_release_candidate_ready"

    def status_for(self, observation: ProductionReleaseCandidateObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason in {"market_regime_required", "live_execution_not_allowed_for_release_candidate"}:
            return "BLOCKED"
        if reason == "production_release_candidate_ready":
            return "READY"
        return "REVIEW"
