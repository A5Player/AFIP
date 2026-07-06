"""Runtime scoring for macro market factors."""

from __future__ import annotations

from dataclasses import asdict
from typing import Mapping

from .market_factor_snapshot import MarketFactorSnapshot


class MarketFactorRuntime:
    """Convert DXY, yields, and cross-market changes into a gold macro bias."""

    def build_snapshot(self, raw_factors: Mapping[str, object] | None = None) -> MarketFactorSnapshot:
        raw_factors = raw_factors or {}
        return MarketFactorSnapshot(
            dxy_change_percent=self._to_float(raw_factors.get("dxy_change_percent")),
            us10y_change_bps=self._to_float(raw_factors.get("us10y_change_bps")),
            us02y_change_bps=self._to_float(raw_factors.get("us02y_change_bps")),
            real_yield_change_bps=self._to_float(raw_factors.get("real_yield_change_bps")),
            gold_change_percent=self._to_float(raw_factors.get("gold_change_percent")),
            silver_change_percent=self._to_float(raw_factors.get("silver_change_percent")),
            oil_change_percent=self._to_float(raw_factors.get("oil_change_percent")),
            equity_index_change_percent=self._to_float(raw_factors.get("equity_index_change_percent")),
        )

    def evaluate(self, raw_factors: Mapping[str, object] | None = None) -> dict[str, object]:
        snapshot = self.build_snapshot(raw_factors)
        score = 50.0
        reasons: list[str] = []
        if snapshot.dxy_change_percent <= -0.20:
            score += 18.0
            reasons.append("dxy_softness_supports_gold")
        elif snapshot.dxy_change_percent >= 0.20:
            score -= 18.0
            reasons.append("dxy_strength_pressures_gold")
        if snapshot.real_yield_change_bps <= -3.0:
            score += 22.0
            reasons.append("real_yield_decline_supports_gold")
        elif snapshot.real_yield_change_bps >= 3.0:
            score -= 22.0
            reasons.append("real_yield_increase_pressures_gold")
        if snapshot.us10y_change_bps <= -5.0:
            score += 8.0
            reasons.append("us10y_decline_supports_gold")
        elif snapshot.us10y_change_bps >= 5.0:
            score -= 8.0
            reasons.append("us10y_increase_pressures_gold")
        if snapshot.silver_change_percent >= 0.30:
            score += 5.0
            reasons.append("silver_confirmation_supports_gold")
        elif snapshot.silver_change_percent <= -0.30:
            score -= 5.0
            reasons.append("silver_weakness_pressures_gold")
        bounded_score = min(100.0, max(0.0, score))
        if bounded_score >= 65.0:
            gold_bias = "SUPPORTIVE"
        elif bounded_score <= 35.0:
            gold_bias = "PRESSURE"
        else:
            gold_bias = "NEUTRAL"
        return {
            "status": "MARKET_FACTOR_READY",
            "gold_macro_score": round(bounded_score, 2),
            "gold_bias": gold_bias,
            "snapshot": asdict(snapshot),
            "reason": "+".join(reasons) if reasons else "balanced_macro_factors",
        }

    def _to_float(self, value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
