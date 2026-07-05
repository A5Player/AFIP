"""Production Milestone A Pack 9: portfolio resilience index."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class PortfolioResilienceIndexResult:
    """Portfolio resilience result for production allocation quality."""

    status: str
    production_ready: bool
    resilience_score: float
    resilience_state: str
    drawdown_resilience: float
    recovery_quality: float
    exposure_balance: float
    capital_stability: float
    blockers: list[str] = field(default_factory=list)
    reason: str = "portfolio_resilience_index_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_ready": self.production_ready,
            "resilience_score": round(self.resilience_score, 2),
            "resilience_state": self.resilience_state,
            "drawdown_resilience": round(self.drawdown_resilience, 2),
            "recovery_quality": round(self.recovery_quality, 2),
            "exposure_balance": round(self.exposure_balance, 2),
            "capital_stability": round(self.capital_stability, 2),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class PortfolioResilienceIndex:
    """Evaluate whether portfolio state can absorb normal production variance."""

    def evaluate(self, portfolio_state: Mapping[str, Any]) -> PortfolioResilienceIndexResult:
        drawdown_percent = _bounded(portfolio_state.get("drawdown_percent", 0.0), 0.0, 100.0)
        intraday_drawdown_percent = _bounded(portfolio_state.get("intraday_drawdown_percent", drawdown_percent), 0.0, 100.0)
        recovery_factor = _bounded(portfolio_state.get("recovery_factor", 1.0), 0.0, 5.0)
        open_exposure = _bounded(portfolio_state.get("open_exposure", 0.0), 0.0, 2.0)
        maximum_exposure = max(0.01, _bounded(portfolio_state.get("maximum_exposure", 1.0), 0.01, 2.0))
        equity_volatility_percent = _bounded(portfolio_state.get("equity_volatility_percent", 5.0), 0.0, 100.0)

        drawdown_resilience = max(0.0, 100.0 - (drawdown_percent * 5.0 + intraday_drawdown_percent * 3.0))
        recovery_quality = min(100.0, recovery_factor * 55.0)
        exposure_utilization = open_exposure / maximum_exposure
        exposure_balance = max(0.0, 100.0 - abs(exposure_utilization - 0.45) * 120.0)
        capital_stability = max(0.0, 100.0 - equity_volatility_percent * 6.0)

        resilience_score = (
            drawdown_resilience * 0.30
            + recovery_quality * 0.25
            + exposure_balance * 0.25
            + capital_stability * 0.20
        )

        blockers: list[str] = []
        if drawdown_resilience < 55.0:
            blockers.append("drawdown_resilience_below_portfolio_threshold")
        if recovery_quality < 55.0:
            blockers.append("recovery_quality_below_portfolio_threshold")
        if exposure_balance < 45.0:
            blockers.append("exposure_balance_below_portfolio_threshold")
        if capital_stability < 45.0:
            blockers.append("capital_stability_below_portfolio_threshold")

        production_ready = resilience_score >= 60.0 and not blockers
        if resilience_score >= 82.0:
            resilience_state = "HIGH_RESILIENCE"
        elif resilience_score >= 60.0:
            resilience_state = "STANDARD_RESILIENCE"
        else:
            resilience_state = "LOW_RESILIENCE"

        return PortfolioResilienceIndexResult(
            status="READY" if production_ready else "OBSERVE",
            production_ready=production_ready,
            resilience_score=resilience_score,
            resilience_state=resilience_state,
            drawdown_resilience=drawdown_resilience,
            recovery_quality=recovery_quality,
            exposure_balance=exposure_balance,
            capital_stability=capital_stability,
            blockers=blockers,
            reason="portfolio_resilience_ready" if production_ready else "portfolio_resilience_observation_required",
        )


def _bounded(value: Any, lower: float = 0.0, upper: float = 100.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = lower
    return max(lower, min(upper, numeric))
