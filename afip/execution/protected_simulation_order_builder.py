from afip.position.position_sizer import PositionSizer
from afip.protection.adaptive_rr_portfolio import AdaptiveRRProtectionPlanner
from afip.position_policy import confidence_maximum_units


class ProtectedSimulationOrderBuilder:
    """Create a simulation order carrying a per-unit adaptive RR portfolio."""

    def __init__(self, sizer=None, planner=None):
        self.sizer = sizer or PositionSizer()
        self.planner = planner or AdaptiveRRProtectionPlanner()

    @staticmethod
    def _confidence_units(confidence: float) -> int:
        return confidence_maximum_units(confidence).maximum_units

    def build(self, decision: dict, snapshot: dict, balance: float = 1000.0) -> dict:
        action = str(decision.get("action", "WAIT")).upper()
        if action not in ("BUY", "SELL"):
            return {"status": "NO_ORDER", "reason": decision.get("reason", "no_trade_action")}

        closes = snapshot.get("closes", [])
        entry_price = float(closes[-1]) if closes else float(snapshot.get("entry_price", 0.0) or 0.0)
        confidence = float(decision.get("confidence", 0.0) or 0.0)
        unit_count = self._confidence_units(confidence)

        # Backward-compatible simulation allocation is intentionally narrow.
        # It is available only when ConfidenceCalibrator explicitly marks a
        # legacy SIMULATION decision that has already passed RiskAssessor.
        compatibility_policy = str(decision.get("execution_policy", "")).upper()
        compatibility_units = int(decision.get("simulation_compatibility_units", 0) or 0)
        if (
            unit_count <= 0
            and compatibility_policy == "LEGACY_SIMULATION_COMPATIBILITY"
            and bool(decision.get("risk", {}).get("allowed", False))
            and compatibility_units == 1
        ):
            unit_count = 1

        if unit_count <= 0:
            return {"status": "NO_ORDER", "reason": "confidence_below_rr_unit_threshold"}

        sizing = self.sizer.calculate(balance=balance)
        profile_id = str(snapshot.get("profile_id", decision.get("profile_id", "P2"))).upper()
        regime = str(snapshot.get("market_regime", decision.get("market_regime", "UNKNOWN")))
        research = snapshot.get("protection_research") or decision.get("protection_research") or {}
        point_size = float(snapshot.get("point_size", 0.01) or 0.01)
        portfolio = self.planner.plan_portfolio(
            action=action,
            entry_price=entry_price,
            unit_count=unit_count,
            profile_id=profile_id,
            confidence=confidence,
            snapshot=snapshot,
            research=research,
            regime=regime,
            point_size=point_size,
        )
        if portfolio.get("status") != "PLANNED":
            return {"status": "NO_ORDER", "reason": portfolio.get("reason", "rr_protection_not_ready")}

        first = portfolio["unit_plans"][0]
        return {
            "status": "SIMULATION_ORDER_READY",
            "symbol": snapshot.get("symbol", "GOLD#"),
            "action": action,
            "entry_price": entry_price,
            "lot": sizing["lot"],
            "sizing": sizing,
            # Compatibility view only. Gateway consumes protection_portfolio.
            "protection": {
                "status": "PLANNED",
                "stop_loss_points": first["stop_loss_points"],
                "take_profit_points": first["take_profit_points"],
                "sl": first["initial_sl"],
                "tp": first["initial_tp"],
            },
            "protection_portfolio": portfolio,
            "live": False,
            "decision": decision,
            "unit_allocation": {
                "approved_units": unit_count,
                "source": (
                    "LEGACY_SIMULATION_COMPATIBILITY"
                    if compatibility_policy == "LEGACY_SIMULATION_COMPATIBILITY"
                    else "CONFIDENCE_MAXIMUM_UNIT_POLICY"
                ),
                "confidence": confidence,
            },
        }
