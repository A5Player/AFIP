from afip.position.position_sizer import PositionSizer
from afip.protection.sl_tp_planner import SLTPPlanner

class ProtectedSimulationOrderBuilder:
    def __init__(self, sizer=None, planner=None):
        self.sizer = sizer or PositionSizer()
        self.planner = planner or SLTPPlanner()

    def build(self, decision: dict, snapshot: dict, balance: float = 1000.0) -> dict:
        action = decision.get("action", "WAIT")
        if action not in ("BUY", "SELL"):
            return {"status": "NO_ORDER", "reason": decision.get("reason", "no_trade_action")}

        closes = snapshot.get("closes", [])
        entry_price = closes[-1] if closes else 0.0

        sizing = self.sizer.calculate(balance=balance)
        protection = self.planner.plan(action=action, entry_price=entry_price)

        return {
            "status": "SIMULATION_ORDER_READY",
            "symbol": snapshot.get("symbol", "XAUUSD"),
            "action": action,
            "entry_price": entry_price,
            "lot": sizing["lot"],
            "sizing": sizing,
            "protection": protection,
            "live": False,
            "decision": decision,
        }
