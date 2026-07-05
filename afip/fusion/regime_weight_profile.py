"""Market regime weight profiles for AFIP Milestone B."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegimeWeightProfileResult:
    """Market-regime financial allocation profile."""

    status: str
    regime: str
    weights: dict[str, float]
    reason: str


class RegimeWeightProfile:
    """Return production-safe baseline weights for the detected market regime."""

    _profiles: dict[str, dict[str, float]] = {
        "TREND": {"TREND": 0.34, "MOMENTUM": 0.24, "LIQUIDITY": 0.14, "EXECUTION": 0.14, "RISK": 0.14},
        "RANGE": {"LIQUIDITY": 0.30, "STRUCTURE": 0.24, "EXECUTION": 0.18, "RISK": 0.18, "MOMENTUM": 0.10},
        "VOLATILITY": {"RISK": 0.32, "EXECUTION": 0.26, "LIQUIDITY": 0.18, "STRUCTURE": 0.14, "TREND": 0.10},
        "NEWS": {"RISK": 0.38, "EXECUTION": 0.32, "LIQUIDITY": 0.14, "VOLATILITY": 0.10, "TREND": 0.06},
    }

    def resolve(self, regime: str) -> RegimeWeightProfileResult:
        regime_key = str(regime or "BALANCED").upper()
        profile = self._profiles.get(regime_key)
        if profile is None:
            profile = {"TREND": 0.20, "MOMENTUM": 0.18, "LIQUIDITY": 0.20, "EXECUTION": 0.20, "RISK": 0.22}
            regime_key = "BALANCED"
        return RegimeWeightProfileResult(
            status="REGIME_WEIGHT_PROFILE_READY",
            regime=regime_key,
            weights=dict(profile),
            reason=f"{regime_key.lower()}_financial_weight_profile",
        )
