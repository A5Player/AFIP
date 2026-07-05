class SimulationOrderBuilder:
    def build(self, decision: dict, symbol: str = "XAUUSD", lot: float = 0.01) -> dict:
        action = decision.get("action", "WAIT")
        if action not in ("BUY", "SELL"):
            return {
                "status": "NO_ORDER",
                "reason": decision.get("reason", "no_trade_action"),
                "decision": decision,
            }

        return {
            "status": "SIMULATION_ORDER_READY",
            "symbol": symbol,
            "action": action,
            "lot": lot,
            "confidence": decision.get("confidence", 0),
            "live": False,
            "decision": decision,
        }
