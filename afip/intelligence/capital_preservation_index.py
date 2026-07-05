"""Production Milestone A Pack 7: capital preservation index.

Additive capital preservation intelligence for production portfolio decisions.
This module uses international financial terminology only and preserves
backward compatibility with all earlier Milestone A packs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class CapitalPreservationIndexResult:
    """Capital preservation result for drawdown-aware production decisions."""

    status: str
    preservation_score: float
    drawdown_resilience_score: float
    equity_stability_score: float
    recovery_quality_score: float
    capital_state: str
    production_ready: bool
    blockers: list[str] = field(default_factory=list)
    reason: str = "capital_preservation_index_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "preservation_score": round(self.preservation_score, 2),
            "drawdown_resilience_score": round(self.drawdown_resilience_score, 2),
            "equity_stability_score": round(self.equity_stability_score, 2),
            "recovery_quality_score": round(self.recovery_quality_score, 2),
            "capital_state": self.capital_state,
            "production_ready": self.production_ready,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class CapitalPreservationIndex:
    """Evaluates capital preservation using drawdown, equity stability, and recovery."""

    def evaluate(self, portfolio_state: Mapping[str, Any]) -> CapitalPreservationIndexResult:
        drawdown_percent = float(portfolio_state.get("drawdown_percent", 0.0))
        intraday_drawdown_percent = float(portfolio_state.get("intraday_drawdown_percent", drawdown_percent))
        equity_volatility_percent = float(portfolio_state.get("equity_volatility_percent", 4.0))
        recovery_factor = float(portfolio_state.get("recovery_factor", 1.0))
        realized_profit_factor = float(portfolio_state.get("realized_profit_factor", 1.0))

        drawdown_resilience = _clamp(100.0 - drawdown_percent * 4.2 - intraday_drawdown_percent * 1.8)
        equity_stability = _clamp(100.0 - equity_volatility_percent * 6.0)
        recovery_quality = _clamp(45.0 + recovery_factor * 20.0 + (realized_profit_factor - 1.0) * 18.0)
        preservation_score = (drawdown_resilience * 0.45) + (equity_stability * 0.25) + (recovery_quality * 0.30)

        blockers: list[str] = []
        if drawdown_percent > 18.0:
            blockers.append("drawdown_above_capital_preservation_threshold")
        if intraday_drawdown_percent > 12.0:
            blockers.append("intraday_drawdown_above_capital_preservation_threshold")
        if equity_volatility_percent > 11.0:
            blockers.append("equity_volatility_elevated")
        if recovery_factor < 0.65:
            blockers.append("recovery_quality_below_production_threshold")
        if preservation_score < 62.0:
            blockers.append("capital_preservation_score_low")

        if preservation_score >= 82.0 and not blockers:
            capital_state = "RESILIENT"
        elif preservation_score >= 68.0 and not blockers:
            capital_state = "STABLE"
        else:
            capital_state = "CONSERVATIVE"

        production_ready = not blockers and preservation_score >= 68.0
        return CapitalPreservationIndexResult(
            status="READY" if production_ready else "OBSERVE",
            preservation_score=preservation_score,
            drawdown_resilience_score=drawdown_resilience,
            equity_stability_score=equity_stability,
            recovery_quality_score=recovery_quality,
            capital_state=capital_state,
            production_ready=production_ready,
            blockers=blockers,
            reason="capital_preservation_index_ready" if production_ready else "capital_preservation_index_observation_required",
        )
