"""Paper trading profile for Production Milestone G Pack 6."""

from __future__ import annotations

from dataclasses import dataclass

from .paper_observation import PaperTradingObservation


@dataclass(frozen=True)
class PaperTradingProfile:
    """Deterministic profile summarizing paper trading readiness."""

    market_regime: str
    signal_context: str
    runtime_component: str
    execution_mode: str
    configuration_version: str
    decision_action: str
    decision_confidence: float
    production_hardening_score: float
    risk_allowed: bool
    trading_cost_score: float
    paper_account_equity: float
    simulated_lot: float
    max_drawdown: float
    paper_quality: float
    continuity_score: float
    status: str
    review_required: bool
    reason: str

    @classmethod
    def from_observation(cls, observation: PaperTradingObservation, status: str, reason: str) -> "PaperTradingProfile":
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            runtime_component=observation.runtime_component,
            execution_mode=observation.execution_mode,
            configuration_version=observation.configuration_version,
            decision_action=observation.decision_action,
            decision_confidence=round(observation.decision_confidence, 4),
            production_hardening_score=round(observation.production_hardening_score, 4),
            risk_allowed=observation.risk_allowed,
            trading_cost_score=round(observation.trading_cost_score, 4),
            paper_account_equity=round(observation.paper_account_equity, 2),
            simulated_lot=round(observation.simulated_lot, 4),
            max_drawdown=round(observation.max_drawdown, 4),
            paper_quality=round(observation.paper_quality, 4),
            continuity_score=round(observation.continuity_score, 4),
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
        return "PAPER_TRADING_READY"
