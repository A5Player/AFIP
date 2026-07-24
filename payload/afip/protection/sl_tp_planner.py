from __future__ import annotations


class SLTPPlanner:
    def plan(
        self, action: str, entry_price: float,
        stop_loss_points: float | None = None,
        take_profit_points: float | None = None,
        point_size: float = 0.01,
    ) -> dict:
        if action not in ("BUY", "SELL"):
            return {"status": "NO_PLAN", "reason": "no_trade_action"}
        if stop_loss_points is None or take_profit_points is None:
            return {"status": "NO_PLAN", "reason": "adaptive_protection_required"}
        stop_loss_points = float(stop_loss_points)
        take_profit_points = float(take_profit_points)
        if stop_loss_points <= 0 or take_profit_points <= 0 or point_size <= 0:
            return {"status": "NO_PLAN", "reason": "invalid_protection_distance"}
        if abs(stop_loss_points - 3000.0) < 1e-9 and abs(take_profit_points - 500.0) < 1e-9:
            return {"status": "NO_PLAN", "reason": "legacy_fixed_sl_tp_fallback_rejected"}
        distance_sl = stop_loss_points * point_size
        distance_tp = take_profit_points * point_size
        if action == "BUY":
            sl, tp = entry_price - distance_sl, entry_price + distance_tp
        else:
            sl, tp = entry_price + distance_sl, entry_price - distance_tp
        return {
            "status": "PLANNED", "action": action, "entry_price": entry_price,
            "sl": round(sl, 5), "tp": round(tp, 5),
            "stop_loss_points": stop_loss_points, "take_profit_points": take_profit_points,
        }
