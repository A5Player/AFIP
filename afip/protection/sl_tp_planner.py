class SLTPPlanner:
    def plan(self, action: str, entry_price: float, stop_loss_points: float = 3000.0, take_profit_points: float = 500.0, point_size: float = 0.01) -> dict:
        if action not in ("BUY", "SELL"):
            return {"status": "NO_PLAN", "reason": "no_trade_action"}

        distance_sl = stop_loss_points * point_size
        distance_tp = take_profit_points * point_size

        if action == "BUY":
            sl = entry_price - distance_sl
            tp = entry_price + distance_tp
        else:
            sl = entry_price + distance_sl
            tp = entry_price - distance_tp

        return {
            "status": "PLANNED",
            "action": action,
            "entry_price": entry_price,
            "sl": round(sl, 5),
            "tp": round(tp, 5),
            "stop_loss_points": stop_loss_points,
            "take_profit_points": take_profit_points,
        }
