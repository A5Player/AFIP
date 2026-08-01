import pytest

from afip.execution.protected_simulation_order_builder import ProtectedSimulationOrderBuilder


class _Planner:
    def plan_portfolio(self, **_kwargs):
        return {
            "status": "PLANNED",
            "unit_plans": [{
                "stop_loss_points": 812.0,
                "take_profit_points": 1624.0,
                "initial_sl": 2391.88,
                "initial_tp": 2416.24,
            }],
        }


class _Sizer:
    def __init__(self):
        self.received = None

    def calculate(self, **kwargs):
        self.received = kwargs
        return {"lot": 0.01, **kwargs}


def _decision(**changes):
    value = {
        "action": "BUY", "confidence": 98.0, "requested_units": 1,
        "approved_units": 1, "approved_risk_usd": 8.12,
    }
    value.update(changes)
    return value


def _snapshot(**changes):
    value = {"symbol": "GOLD#", "entry_price": 2400.0, "point_size": 0.01}
    value.update(changes)
    return value


def test_execution_uses_explicit_authority_result():
    sizer = _Sizer()
    result = ProtectedSimulationOrderBuilder(sizer=sizer, planner=_Planner()).build(_decision(), _snapshot())
    assert result["status"] == "SIMULATION_ORDER_READY"
    assert sizer.received == {"balance": 1000.0, "risk_usd": 8.12, "stop_loss_points": 812.0}
    assert result["sizing"]["risk_usd"] == 8.12
    assert result["sizing"]["stop_loss_points"] == 812.0


def test_missing_approved_risk_blocks_before_sizing():
    sizer = _Sizer()
    result = ProtectedSimulationOrderBuilder(sizer=sizer, planner=_Planner()).build(_decision(approved_risk_usd=None), _snapshot())
    assert result == {"status": "NO_ORDER", "reason": "approved_risk_authority_unavailable"}
    assert sizer.received is None
