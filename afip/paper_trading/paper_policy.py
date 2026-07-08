"""Paper trading policy for deterministic simulation readiness review."""

from __future__ import annotations

from dataclasses import dataclass

from .paper_observation import PaperTradingObservation


@dataclass(frozen=True)
class PaperTradingPolicy:
    """Deterministic gate that keeps paper trading separate from live execution."""

    minimum_decision_confidence: float = 0.58
    minimum_hardening_score: float = 0.72
    minimum_trading_cost_score: float = 0.60
    maximum_drawdown: float = 0.30
    minimum_paper_quality: float = 0.72
    minimum_continuity_score: float = 0.74

    def evaluate_reason(self, observation: PaperTradingObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.simulation_only:
            return "live_execution_not_allowed_for_paper_trading"
        if not observation.actionable_decision:
            return "decision_action_required"
        if not observation.account_ready:
            return "paper_account_required"
        if not observation.risk_allowed:
            return "risk_not_allowed"
        if observation.decision_confidence < self.minimum_decision_confidence:
            return "decision_confidence_review_required"
        if observation.production_hardening_score < self.minimum_hardening_score:
            return "production_hardening_review_required"
        if observation.trading_cost_score < self.minimum_trading_cost_score:
            return "trading_cost_review_required"
        if observation.max_drawdown > self.maximum_drawdown:
            return "paper_drawdown_review_required"
        if observation.paper_quality < self.minimum_paper_quality:
            return "paper_quality_review_required"
        if observation.continuity_score < self.minimum_continuity_score:
            return "paper_continuity_review_required"
        return "paper_trading_ready"

    def status_for(self, observation: PaperTradingObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason in {"market_regime_required", "live_execution_not_allowed_for_paper_trading"}:
            return "BLOCKED"
        if reason == "paper_trading_ready":
            return "READY"
        return "REVIEW"
