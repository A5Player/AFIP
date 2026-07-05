"""
AFIP — Trading Cost Intelligence.

Evaluates GOLD# spread in broker points before any simulated execution decision
is accepted. This component is read-only and execution remains locked to
simulation mode.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TradingCostProfile:
    caution_spread_points: float = 25.0
    max_spread_points: float = 35.0


class TradingCostIntelligence:
    """Evaluates execution cost quality from the current broker spread."""

    def __init__(self, profile: TradingCostProfile | None = None):
        self.profile = profile or TradingCostProfile()

    def assess(self, snapshot: dict | None, connection: dict | None = None) -> dict:
        snapshot = snapshot or {}
        connection = connection or {}
        spread = self._spread(snapshot, connection)
        max_spread = float(self.profile.max_spread_points)
        caution_spread = float(self.profile.caution_spread_points)

        if spread > max_spread:
            status = "BLOCK"
            allowed = False
            reason = "spread_above_maximum"
        elif spread >= caution_spread:
            status = "CAUTION"
            allowed = True
            reason = "spread_near_limit"
        else:
            status = "PASS"
            allowed = True
            reason = "trading_cost_pass"

        cost_score = max(0.0, min(100.0, 100.0 - (spread / max_spread * 100.0))) if max_spread else 0.0
        return {
            "name": "TradingCostIntelligence",
            "status": status,
            "allowed": allowed,
            "spread_points": round(spread, 2),
            "caution_spread_points": caution_spread,
            "max_spread_points": max_spread,
            "cost_score": round(cost_score, 2),
            "reason": reason,
            "execution": "LOCKED_SIMULATION_ONLY",
        }

    @staticmethod
    def _spread(snapshot: dict, connection: dict) -> float:
        for source in (snapshot, connection):
            try:
                return float(source.get("spread"))
            except (TypeError, ValueError):
                continue
        return 999.0
