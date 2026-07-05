from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class VolatilityWeightProfileResult:
    status: str
    volatility_regime: str
    weights: dict[str, float]
    dominant_category: str
    reason: str


class VolatilityWeightProfile:
    """Provide allocation profile adjustments for volatility conditions."""

    _PROFILES: Mapping[str, Mapping[str, float]] = {
        "LOW": {"TREND": 0.28, "MOMENTUM": 0.22, "LIQUIDITY": 0.18, "EXECUTION": 0.14, "RISK": 0.18},
        "NORMAL": {"TREND": 0.25, "MOMENTUM": 0.20, "LIQUIDITY": 0.20, "EXECUTION": 0.15, "RISK": 0.20},
        "HIGH": {"TREND": 0.16, "MOMENTUM": 0.14, "LIQUIDITY": 0.22, "EXECUTION": 0.23, "RISK": 0.25},
        "EXTREME": {"TREND": 0.10, "MOMENTUM": 0.10, "LIQUIDITY": 0.20, "EXECUTION": 0.28, "RISK": 0.32},
    }

    def resolve(self, volatility_regime: str) -> VolatilityWeightProfileResult:
        regime = (volatility_regime or "NORMAL").upper()
        weights = dict(self._PROFILES.get(regime, self._PROFILES["NORMAL"]))
        resolved = regime if regime in self._PROFILES else "NORMAL"
        dominant = max(weights, key=weights.get)
        return VolatilityWeightProfileResult(
            status="VOLATILITY_WEIGHT_PROFILE_READY",
            volatility_regime=resolved,
            weights=weights,
            dominant_category=dominant,
            reason="volatility_profile_resolved",
        )
