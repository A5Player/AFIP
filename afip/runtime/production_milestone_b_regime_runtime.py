from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from afip.fusion.regime_weight_integration import RegimeWeightIntegration


@dataclass(frozen=True)
class ProductionMilestoneBRegimeRuntimeResult:
    status: str
    current_regime: str
    volatility_regime: str
    dominant_category: str
    weights: dict[str, float]
    transition_risk: float
    execution_mode: str
    reason: str


class ProductionMilestoneBRegimeRuntime:
    """Production runtime for regime-based adaptive allocation."""

    def __init__(self) -> None:
        self._integration = RegimeWeightIntegration()

    def run(
        self,
        previous_regime: str = "BALANCED",
        current_regime: str = "BALANCED",
        volatility_regime: str = "NORMAL",
        performance_tilt: Mapping[str, float] | None = None,
    ) -> ProductionMilestoneBRegimeRuntimeResult:
        integration = self._integration.integrate(previous_regime, current_regime, volatility_regime, performance_tilt)
        execution_mode = self._resolve_execution_mode(integration.transition_risk, integration.dominant_category)
        return ProductionMilestoneBRegimeRuntimeResult(
            status="MILESTONE_B_REGIME_RUNTIME_READY" if integration.weights else "MILESTONE_B_REGIME_RUNTIME_REVIEW",
            current_regime=integration.current_regime,
            volatility_regime=integration.volatility_regime,
            dominant_category=integration.dominant_category,
            weights=integration.weights,
            transition_risk=integration.transition_risk,
            execution_mode=execution_mode,
            reason="regime_runtime_allocation_ready" if integration.weights else "regime_runtime_allocation_review",
        )

    @staticmethod
    def _resolve_execution_mode(transition_risk: float, dominant_category: str) -> str:
        if transition_risk >= 0.80:
            return "CAPITAL_PRESERVATION"
        if dominant_category in {"RISK", "EXECUTION"}:
            return "CONTROLLED_EXECUTION"
        return "STANDARD_EXECUTION"
