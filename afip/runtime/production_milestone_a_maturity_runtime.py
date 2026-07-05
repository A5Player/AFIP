"""Production Milestone A Pack 6: maturity runtime integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from afip.intelligence.market_regime_consistency_index import MarketRegimeConsistencyIndex
from afip.intelligence.portfolio_maturity_index import PortfolioMaturityIndex
from afip.learning.optimization_drift_index import OptimizationDriftIndex
from afip.runtime.production_milestone_a_portfolio_runtime import ProductionMilestoneAPortfolioRuntime


@dataclass(frozen=True)
class ProductionMilestoneAMaturityRuntimeResult:
    """Integrated Pack 6 result for maturity-aware production decisions."""

    status: str
    production_allowed: bool
    action: str
    confidence: float
    maturity_tier: str
    market_state: str
    drift_status: str
    portfolio_runtime: Dict[str, Any]
    portfolio_maturity: Dict[str, Any]
    regime_consistency: Dict[str, Any]
    optimization_drift: Dict[str, Any]
    blockers: list[str] = field(default_factory=list)
    reason: str = "production_milestone_a_maturity_runtime_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_allowed": self.production_allowed,
            "action": self.action,
            "confidence": round(self.confidence, 2),
            "maturity_tier": self.maturity_tier,
            "market_state": self.market_state,
            "drift_status": self.drift_status,
            "portfolio_runtime": dict(self.portfolio_runtime),
            "portfolio_maturity": dict(self.portfolio_maturity),
            "regime_consistency": dict(self.regime_consistency),
            "optimization_drift": dict(self.optimization_drift),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class ProductionMilestoneAMaturityRuntime:
    """Additive maturity runtime combining portfolio, market, and learning checks."""

    def __init__(self) -> None:
        self.portfolio_runtime = ProductionMilestoneAPortfolioRuntime()
        self.portfolio_maturity = PortfolioMaturityIndex()
        self.regime_consistency = MarketRegimeConsistencyIndex()
        self.optimization_drift = OptimizationDriftIndex()

    def evaluate(self, context: Mapping[str, Any]) -> ProductionMilestoneAMaturityRuntimeResult:
        portfolio_runtime = self.portfolio_runtime.evaluate(context).to_dict()
        maturity = self.portfolio_maturity.evaluate(context.get("portfolio_state", {})).to_dict()
        consistency = self.regime_consistency.evaluate(context.get("regime_history", [])).to_dict()
        drift = self.optimization_drift.evaluate(
            context.get("optimization_parameters", {}),
            context.get("baseline_parameters", context.get("base_thresholds", {})),
        ).to_dict()

        blockers: list[str] = []
        if not portfolio_runtime["production_allowed"]:
            blockers.extend(f"portfolio_runtime:{item}" for item in portfolio_runtime.get("blockers", []))
        if not maturity["production_ready"]:
            blockers.extend(f"portfolio_maturity:{item}" for item in maturity.get("blockers", []))
        if not consistency["production_ready"]:
            blockers.extend(f"regime_consistency:{item}" for item in consistency.get("blockers", []))
        if not drift["optimization_allowed"]:
            blockers.extend(f"optimization_drift:{item}" for item in drift.get("blockers", []))

        production_allowed = not blockers and portfolio_runtime["production_allowed"]
        return ProductionMilestoneAMaturityRuntimeResult(
            status="READY" if production_allowed else "OBSERVE",
            production_allowed=production_allowed,
            action=portfolio_runtime["action"] if production_allowed else "HOLD",
            confidence=portfolio_runtime["confidence"] if production_allowed else min(float(portfolio_runtime.get("confidence", 0.0)), 50.0),
            maturity_tier=maturity["maturity_tier"],
            market_state=consistency["market_state"],
            drift_status=drift["drift_status"],
            portfolio_runtime=portfolio_runtime,
            portfolio_maturity=maturity,
            regime_consistency=consistency,
            optimization_drift=drift,
            blockers=blockers,
            reason="production_milestone_a_maturity_runtime_ready" if production_allowed else "production_milestone_a_maturity_runtime_observation_required",
        )
