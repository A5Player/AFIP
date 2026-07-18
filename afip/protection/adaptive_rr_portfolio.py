"""Adaptive multi-unit Risk-Reward protection portfolio.

R means Risk-Reward (RR), not a time horizon.  The planner is deterministic,
research-aware, and has no execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from statistics import median
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class RRUnitPlan:
    role: str
    rr_target: float
    stop_loss_points: float
    take_profit_points: float
    initial_sl: float
    initial_tp: float
    maximum_giveback_r: float
    break_even_trigger_r: float
    profit_lock_trigger_r: float
    trailing_start_r: float
    research_basis: str
    decision_reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class AdaptiveRRProtectionPlanner:
    """Build per-unit SL/TP plans from research, structure and volatility.

    Priority: validated research evidence -> market structure/volatility ->
    conservative deterministic fallback.  Risk distance is chosen first;
    TP is then derived from the selected RR target.
    """

    ROLE_ORDER = ("RR_NEAR", "RR_CORE", "RR_RUNNER")
    DEFAULT_RR = (1.0, 2.0, 3.0)
    PROFILE_GIVEBACK = {
        "P1": (0.20, 0.35, 0.50),
        "P2": (0.25, 0.45, 0.70),
        "P3": (0.30, 0.60, 0.90),
        "P4": (0.50, 1.00, 1.50),
    }

    @staticmethod
    def _number(value: Any, default: float = 0.0) -> float:
        try:
            number = float(value)
            return number if number > 0 else default
        except (TypeError, ValueError):
            return default

    @classmethod
    def _rr_targets(cls, research: Mapping[str, Any], regime: str) -> tuple[float, float, float]:
        raw = research.get("validated_rr_targets") or research.get("rr_targets")
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            values = tuple(cls._number(v) for v in raw)
            values = tuple(v for v in values if 0.25 <= v <= 20.0)
            if len(values) >= 3:
                return tuple(sorted(values[:3]))  # type: ignore[return-value]
        regime_key = regime.strip().upper()
        if "TREND" in regime_key:
            return (1.0, 2.5, 4.0)
        if "RANGE" in regime_key or "MEAN_REVERSION" in regime_key:
            return (0.8, 1.3, 2.0)
        if "BREAKOUT" in regime_key:
            return (1.2, 2.5, 4.5)
        return cls.DEFAULT_RR

    @classmethod
    def _stop_points(
        cls,
        snapshot: Mapping[str, Any],
        research: Mapping[str, Any],
        point_size: float,
    ) -> tuple[float, str]:
        validated = bool(research.get("validated", False))
        sample_size = int(cls._number(research.get("sample_size"), 0.0))
        researched = cls._number(
            research.get("recommended_stop_points", research.get("median_adverse_excursion_points")),
            0.0,
        )
        if validated and sample_size >= 30 and researched > 0:
            return round(researched, 2), "VALIDATED_RESEARCH"

        explicit = cls._number(snapshot.get("structural_stop_points"), 0.0)
        if explicit > 0:
            return round(explicit, 2), "MARKET_STRUCTURE"

        atr_points = cls._number(snapshot.get("atr_points"), 0.0)
        if atr_points > 0:
            return round(max(50.0, atr_points * 1.5), 2), "ATR_VOLATILITY"

        closes = snapshot.get("closes") or ()
        if isinstance(closes, Sequence) and len(closes) >= 6 and point_size > 0:
            values = [float(v) for v in closes[-21:]]
            moves = [abs(values[i] - values[i - 1]) / point_size for i in range(1, len(values))]
            realized = median(moves) if moves else 0.0
            if realized > 0:
                return round(max(50.0, min(3000.0, realized * 3.0)), 2), "REALIZED_VOLATILITY"

        # Safe non-zero fallback only when no research/structure/volatility exists.
        # It is explicitly tagged so learning and certification can reject it.
        return 500.0, "EVIDENCE_INSUFFICIENT_FALLBACK"

    def plan_portfolio(
        self,
        *,
        action: str,
        entry_price: float,
        unit_count: int,
        profile_id: str,
        confidence: float,
        snapshot: Mapping[str, Any],
        research: Mapping[str, Any] | None = None,
        regime: str = "UNKNOWN",
        point_size: float = 0.01,
    ) -> dict[str, Any]:
        action = str(action).upper()
        if action not in {"BUY", "SELL"} or unit_count <= 0 or entry_price <= 0 or point_size <= 0:
            return {"status": "NO_PLAN", "reason": "invalid_rr_portfolio_request", "unit_plans": []}

        evidence = research or {}
        sl_points, basis = self._stop_points(snapshot, evidence, point_size)
        rr_targets = self._rr_targets(evidence, regime)
        giveback = self.PROFILE_GIVEBACK.get(profile_id.upper(), self.PROFILE_GIVEBACK["P2"])

        # With fewer than three units, choose the evidence-appropriate diversified set.
        if unit_count == 1:
            indexes = (1,) if "TREND" not in regime.upper() else (2,)
        elif unit_count == 2:
            indexes = (0, 2) if "TREND" in regime.upper() or "BREAKOUT" in regime.upper() else (0, 1)
        else:
            indexes = (0, 1, 2)

        plans: list[dict[str, Any]] = []
        distance_sl = sl_points * point_size
        for index in indexes[:unit_count]:
            rr = rr_targets[index]
            tp_points = round(sl_points * rr, 2)
            distance_tp = tp_points * point_size
            initial_sl = entry_price - distance_sl if action == "BUY" else entry_price + distance_sl
            initial_tp = entry_price + distance_tp if action == "BUY" else entry_price - distance_tp
            plan = RRUnitPlan(
                role=self.ROLE_ORDER[index],
                rr_target=rr,
                stop_loss_points=sl_points,
                take_profit_points=tp_points,
                initial_sl=round(initial_sl, 5),
                initial_tp=round(initial_tp, 5),
                maximum_giveback_r=giveback[index],
                break_even_trigger_r=round(max(0.6, rr * 0.45), 2),
                profit_lock_trigger_r=round(max(0.9, rr * 0.65), 2),
                trailing_start_r=round(max(1.0, rr * 0.80), 2),
                research_basis=basis,
                decision_reason=(
                    f"{self.ROLE_ORDER[index]} selected at {rr:.2f}RR; confidence={confidence:.2f}; "
                    f"regime={regime}; stop_basis={basis}"
                ),
            )
            plans.append(plan.as_dict())

        return {
            "status": "PLANNED",
            "reason": "adaptive_rr_protection_portfolio_ready",
            "rr_definition": "reward_distance / initial_risk_distance",
            "profile_id": profile_id.upper(),
            "confidence": round(float(confidence), 4),
            "regime": regime,
            "stop_basis": basis,
            "research_evidence_sufficient": basis == "VALIDATED_RESEARCH",
            "unit_plans": plans,
            "management_policy": {
                "allow_independent_unit_exit": True,
                "allow_break_even": True,
                "allow_profit_lock": True,
                "allow_structure_trailing": True,
                "forbid_unjustified_peak_profit_to_loss": True,
                "record_peak_r_and_giveback_r": True,
                "post_exit_follow_up_timeframes": ["M30", "H1", "H4", "D1"],
            },
        }
