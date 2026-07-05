"""Production Milestone A Pack 3: market regime exposure control."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from afip.intelligence.adaptive_intelligence_core import clamp


@dataclass(frozen=True)
class RegimeExposureDecision:
    """Production exposure decision derived from market regime conditions."""

    status: str
    exposure_level: str
    exposure_multiplier: float
    action_bias: str
    blockers: list[str] = field(default_factory=list)
    reason: str = "regime_exposure_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "exposure_level": self.exposure_level,
            "exposure_multiplier": round(self.exposure_multiplier, 4),
            "action_bias": self.action_bias,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class RegimeExposureController:
    """Converts regime and transition outputs into safe exposure guidance."""

    def evaluate(self, regime: Mapping[str, Any], transition: Mapping[str, Any] | None = None, cost: Mapping[str, Any] | None = None) -> RegimeExposureDecision:
        transition = transition or {}
        cost = cost or {}
        regime_name = str(regime.get("regime", "UNKNOWN"))
        action_bias = str(regime.get("action_bias", "HOLD"))
        confidence = clamp(float(regime.get("confidence", 0.0) or 0.0))
        spread_quality = clamp(float(cost.get("spread_quality", 100.0) or 100.0))
        risk_bias = str(transition.get("risk_bias", "NORMAL_EXPOSURE"))

        blockers: list[str] = []
        multiplier = 1.0
        level = "NORMAL"
        status = "READY"

        if regime_name in {"HIGH_VOLATILITY", "LOW_QUALITY", "UNKNOWN"} or action_bias == "HOLD":
            multiplier = 0.0
            level = "FLAT"
            blockers.append(f"regime_requires_observation:{regime_name}")
        elif risk_bias == "REDUCE_EXPOSURE":
            multiplier = 0.5
            level = "REDUCED"
            blockers.append("regime_transition_reduce_exposure")
        elif confidence >= 75.0:
            multiplier = 1.0
            level = "NORMAL"
        else:
            multiplier = 0.75
            level = "CAUTIOUS"

        if spread_quality < 45.0:
            multiplier = min(multiplier, 0.5)
            level = "REDUCED" if multiplier > 0 else level
            blockers.append("spread_quality_below_production_preference")

        if multiplier <= 0.0:
            status = "OBSERVE"
        elif blockers:
            status = "CAUTION"

        return RegimeExposureDecision(
            status=status,
            exposure_level=level,
            exposure_multiplier=multiplier,
            action_bias=action_bias if multiplier > 0 else "HOLD",
            blockers=blockers,
            reason="regime_exposure_ready" if status == "READY" else "regime_exposure_protective",
        )
