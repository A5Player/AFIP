"""Production Milestone A Pack 8: liquidity efficiency index."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


@dataclass(frozen=True)
class LiquidityEfficiencyIndexResult:
    """Liquidity efficiency result for production execution quality."""

    status: str
    production_ready: bool
    efficiency_score: float
    efficiency_state: str
    spread_quality: float
    depth_quality: float
    fill_probability: float
    execution_cost_quality: float
    blockers: list[str] = field(default_factory=list)
    reason: str = "liquidity_efficiency_index_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "production_ready": self.production_ready,
            "efficiency_score": round(self.efficiency_score, 2),
            "efficiency_state": self.efficiency_state,
            "spread_quality": round(self.spread_quality, 2),
            "depth_quality": round(self.depth_quality, 2),
            "fill_probability": round(self.fill_probability, 2),
            "execution_cost_quality": round(self.execution_cost_quality, 2),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class LiquidityEfficiencyIndex:
    """Evaluate whether liquidity conditions are efficient enough for production."""

    def evaluate(self, execution_state: Mapping[str, Any]) -> LiquidityEfficiencyIndexResult:
        spread_quality = _bounded(execution_state.get("spread_quality", 50.0))
        depth_quality = _bounded(execution_state.get("depth_quality", execution_state.get("liquidity_score", 50.0)))
        fill_probability = _bounded(execution_state.get("fill_probability", 50.0))
        execution_cost_quality = _bounded(execution_state.get("execution_cost_quality", execution_state.get("slippage_quality", 50.0)))

        efficiency_score = (
            spread_quality * 0.30
            + depth_quality * 0.25
            + fill_probability * 0.25
            + execution_cost_quality * 0.20
        )

        blockers: list[str] = []
        if spread_quality < 55.0:
            blockers.append("spread_quality_below_liquidity_efficiency_threshold")
        if depth_quality < 50.0:
            blockers.append("market_depth_below_liquidity_efficiency_threshold")
        if fill_probability < 55.0:
            blockers.append("fill_probability_below_liquidity_efficiency_threshold")
        if execution_cost_quality < 50.0:
            blockers.append("execution_cost_quality_below_liquidity_efficiency_threshold")

        production_ready = efficiency_score >= 60.0 and not blockers
        if efficiency_score >= 82.0:
            efficiency_state = "HIGH_EFFICIENCY"
        elif efficiency_score >= 60.0:
            efficiency_state = "STANDARD_EFFICIENCY"
        else:
            efficiency_state = "LOW_EFFICIENCY"

        return LiquidityEfficiencyIndexResult(
            status="READY" if production_ready else "OBSERVE",
            production_ready=production_ready,
            efficiency_score=efficiency_score,
            efficiency_state=efficiency_state,
            spread_quality=spread_quality,
            depth_quality=depth_quality,
            fill_probability=fill_probability,
            execution_cost_quality=execution_cost_quality,
            blockers=blockers,
            reason="liquidity_efficiency_ready" if production_ready else "liquidity_efficiency_observation_required",
        )


def _bounded(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 50.0
    return max(0.0, min(100.0, numeric))
