from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from afip.fusion.regime_allocation_blender import RegimeAllocationBlender
from afip.fusion.regime_transition_matrix import RegimeTransitionMatrix
from afip.fusion.regime_weight_profile import RegimeWeightProfile
from afip.fusion.volatility_weight_profile import VolatilityWeightProfile


@dataclass(frozen=True)
class RegimeWeightIntegrationResult:
    status: str
    previous_regime: str
    current_regime: str
    volatility_regime: str
    weights: dict[str, float]
    dominant_category: str
    transition_risk: float
    reason: str


class RegimeWeightIntegration:
    """Integrate market regime, transition risk, and volatility into adaptive weights."""

    def __init__(self) -> None:
        self._regime_profile = RegimeWeightProfile()
        self._volatility_profile = VolatilityWeightProfile()
        self._transition_matrix = RegimeTransitionMatrix()
        self._blender = RegimeAllocationBlender()

    def integrate(
        self,
        previous_regime: str,
        current_regime: str,
        volatility_regime: str,
        performance_tilt: Mapping[str, float] | None = None,
    ) -> RegimeWeightIntegrationResult:
        transition = self._transition_matrix.evaluate(previous_regime, current_regime)
        regime_profile = self._regime_profile.resolve(current_regime)
        volatility_profile = self._volatility_profile.resolve(volatility_regime)
        blended = self._blender.blend(regime_profile.weights, volatility_profile.weights, transition.transition_risk)
        weights = dict(blended.weights)
        if performance_tilt:
            weights = self._apply_performance_tilt(weights, performance_tilt)
        status = "REGIME_WEIGHT_INTEGRATION_READY" if weights else "REGIME_WEIGHT_INTEGRATION_REVIEW"
        dominant = max(weights, key=weights.get) if weights else "NONE"
        return RegimeWeightIntegrationResult(
            status=status,
            previous_regime=transition.previous_regime,
            current_regime=transition.current_regime,
            volatility_regime=volatility_profile.volatility_regime,
            weights=weights,
            dominant_category=dominant,
            transition_risk=transition.transition_risk,
            reason="regime_weight_integration_complete" if weights else "regime_weight_integration_incomplete",
        )

    @staticmethod
    def _apply_performance_tilt(weights: Mapping[str, float], performance_tilt: Mapping[str, float]) -> dict[str, float]:
        adjusted = {}
        for category, weight in weights.items():
            tilt = max(-0.25, min(0.25, float(performance_tilt.get(category, 0.0))))
            adjusted[category] = max(0.0, weight * (1.0 + tilt))
        total = sum(adjusted.values())
        if total <= 0:
            return dict(weights)
        return {category: round(value / total, 4) for category, value in adjusted.items()}
