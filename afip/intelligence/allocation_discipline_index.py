"""Production Milestone A Pack 8: allocation discipline index."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class AllocationDisciplineIndexResult:
    """Allocation discipline result for portfolio-level production control."""

    status: str
    production_ready: bool
    discipline_score: float
    discipline_state: str
    exposure_utilization: float
    concentration_risk: float
    allocation_diversity: float
    drawdown_control: float
    blockers: list[str] = field(default_factory=list)
    reason: str = "allocation_discipline_index_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_ready": self.production_ready,
            "discipline_score": round(self.discipline_score, 2),
            "discipline_state": self.discipline_state,
            "exposure_utilization": round(self.exposure_utilization, 4),
            "concentration_risk": round(self.concentration_risk, 2),
            "allocation_diversity": round(self.allocation_diversity, 2),
            "drawdown_control": round(self.drawdown_control, 2),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class AllocationDisciplineIndex:
    """Evaluate portfolio allocation discipline without changing legacy behavior."""

    def evaluate(self, portfolio_state: Mapping[str, Any]) -> AllocationDisciplineIndexResult:
        open_exposure = max(0.0, _numeric(portfolio_state.get("open_exposure", 0.0)))
        maximum_exposure = max(0.01, _numeric(portfolio_state.get("maximum_exposure", 1.0)))
        exposure_utilization = open_exposure / maximum_exposure

        concentration_risk = _bounded(portfolio_state.get("concentration_risk", exposure_utilization * 100.0))
        allocation_diversity = _bounded(portfolio_state.get("allocation_diversity", 65.0))
        drawdown_percent = max(0.0, _numeric(portfolio_state.get("drawdown_percent", 0.0)))
        intraday_drawdown_percent = max(0.0, _numeric(portfolio_state.get("intraday_drawdown_percent", drawdown_percent)))
        drawdown_control = max(0.0, 100.0 - max(drawdown_percent, intraday_drawdown_percent) * 5.0)

        utilization_quality = max(0.0, 100.0 - max(0.0, exposure_utilization - 0.72) * 140.0)
        concentration_quality = max(0.0, 100.0 - concentration_risk)
        discipline_score = (
            utilization_quality * 0.30
            + concentration_quality * 0.25
            + allocation_diversity * 0.20
            + drawdown_control * 0.25
        )

        blockers: list[str] = []
        if exposure_utilization > 0.92:
            blockers.append("exposure_utilization_above_allocation_discipline_threshold")
        if concentration_risk > 70.0:
            blockers.append("concentration_risk_above_allocation_discipline_threshold")
        if allocation_diversity < 45.0:
            blockers.append("allocation_diversity_below_allocation_discipline_threshold")
        if drawdown_control < 45.0:
            blockers.append("drawdown_control_below_allocation_discipline_threshold")

        production_ready = discipline_score >= 58.0 and not blockers
        if discipline_score >= 82.0:
            discipline_state = "HIGH_DISCIPLINE"
        elif discipline_score >= 58.0:
            discipline_state = "STANDARD_DISCIPLINE"
        else:
            discipline_state = "LOW_DISCIPLINE"

        return AllocationDisciplineIndexResult(
            status="READY" if production_ready else "OBSERVE",
            production_ready=production_ready,
            discipline_score=discipline_score,
            discipline_state=discipline_state,
            exposure_utilization=exposure_utilization,
            concentration_risk=concentration_risk,
            allocation_diversity=allocation_diversity,
            drawdown_control=drawdown_control,
            blockers=blockers,
            reason="allocation_discipline_ready" if production_ready else "allocation_discipline_observation_required",
        )


def _numeric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _bounded(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 50.0
    return max(0.0, min(100.0, numeric))
