"""Production Milestone A Pack 6: portfolio maturity index.

Additive portfolio maturity intelligence for production runtime evaluation.
This module uses international financial terminology only and preserves
backward compatibility with all earlier Milestone A packs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class PortfolioMaturityIndexResult:
    """Portfolio maturity result for production allocation decisions."""

    status: str
    maturity_tier: str
    maturity_score: float
    capital_efficiency_score: float
    drawdown_quality_score: float
    exposure_balance_score: float
    production_ready: bool
    blockers: list[str] = field(default_factory=list)
    reason: str = "portfolio_maturity_index_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "maturity_tier": self.maturity_tier,
            "maturity_score": round(self.maturity_score, 2),
            "capital_efficiency_score": round(self.capital_efficiency_score, 2),
            "drawdown_quality_score": round(self.drawdown_quality_score, 2),
            "exposure_balance_score": round(self.exposure_balance_score, 2),
            "production_ready": self.production_ready,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class PortfolioMaturityIndex:
    """Evaluates portfolio readiness using capital, drawdown, and exposure quality."""

    def evaluate(self, portfolio_state: Mapping[str, Any]) -> PortfolioMaturityIndexResult:
        equity_growth = float(portfolio_state.get("equity_growth", 0.0))
        realized_profit_factor = float(portfolio_state.get("realized_profit_factor", 1.0))
        drawdown_percent = float(portfolio_state.get("drawdown_percent", 0.0))
        open_exposure = float(portfolio_state.get("open_exposure", 0.0))
        maximum_exposure = float(portfolio_state.get("maximum_exposure", 1.0))
        allocation_diversity = float(portfolio_state.get("allocation_diversity", 70.0))

        capital_efficiency = _clamp(55.0 + equity_growth * 1.2 + (realized_profit_factor - 1.0) * 25.0)
        drawdown_quality = _clamp(100.0 - drawdown_percent * 4.0)
        exposure_ratio = 1.0 if maximum_exposure <= 0.0 else open_exposure / maximum_exposure
        exposure_balance = _clamp(100.0 - abs(exposure_ratio - 0.45) * 90.0)
        exposure_balance = (exposure_balance * 0.7) + (_clamp(allocation_diversity) * 0.3)

        maturity_score = (capital_efficiency * 0.35) + (drawdown_quality * 0.40) + (exposure_balance * 0.25)

        blockers: list[str] = []
        if drawdown_percent > 18.0:
            blockers.append("drawdown_quality_below_production_threshold")
        if realized_profit_factor < 0.85:
            blockers.append("capital_efficiency_below_production_threshold")
        if maximum_exposure <= 0.0 or open_exposure > maximum_exposure:
            blockers.append("portfolio_exposure_above_limit")
        if maturity_score < 60.0:
            blockers.append("portfolio_maturity_score_low")

        if maturity_score >= 82.0 and not blockers:
            tier = "ADVANCED"
        elif maturity_score >= 68.0 and not blockers:
            tier = "STANDARD"
        else:
            tier = "DEVELOPING"

        production_ready = not blockers and maturity_score >= 68.0
        return PortfolioMaturityIndexResult(
            status="READY" if production_ready else "OBSERVE",
            maturity_tier=tier,
            maturity_score=maturity_score,
            capital_efficiency_score=capital_efficiency,
            drawdown_quality_score=drawdown_quality,
            exposure_balance_score=exposure_balance,
            production_ready=production_ready,
            blockers=blockers,
            reason="portfolio_maturity_index_ready" if production_ready else "portfolio_maturity_index_observation_required",
        )
