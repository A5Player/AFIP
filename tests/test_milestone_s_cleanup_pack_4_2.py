from afip.execution.protected_simulation_order_builder import ProtectedSimulationOrderBuilder
from afip.risk.confidence_calibrator import ConfidenceCalibrator


def _protected(spread: float = 18.0) -> dict:
    return {
        "mode": "SIMULATION",
        "base": {
            "signal": {
                "snapshots": {
                    "H1": {
                        "symbol": "GOLD#",
                        "spread": spread,
                        "closes": [2300.0, 2301.0, 2302.0],
                    }
                },
                "score": {
                    "buy_score": 0,
                    "sell_score": 0,
                    "overall_confidence": 0,
                    "risk_penalty": 0,
                },
            }
        },
        "protected_order": {"status": "NO_ORDER"},
    }


def _modular(confidence: float = 85.0) -> dict:
    return {
        "decision": {
            "action": "BUY",
            "confidence": confidence,
            "buy_score": confidence,
            "sell_score": 0,
            "penalties": 0,
            "reason": "decision_intelligence_buy_edge",
        }
    }


def test_legacy_simulation_risk_pass_receives_one_compatibility_unit():
    result = ConfidenceCalibrator().calibrate(_protected(), _modular(85), balance=1000)
    order = result["protected_order"]
    assert result["base"]["risk"]["allowed"] is True
    assert order["status"] == "SIMULATION_ORDER_READY"
    assert order["unit_allocation"]["approved_units"] == 1
    assert order["unit_allocation"]["source"] == "LEGACY_SIMULATION_COMPATIBILITY"


def test_direct_builder_does_not_weaken_98_percent_execution_threshold():
    order = ProtectedSimulationOrderBuilder().build(
        {"action": "BUY", "confidence": 85, "risk": {"allowed": True}},
        {"symbol": "GOLD#", "closes": [2300, 2301], "spread": 18},
        balance=1000,
    )
    assert order["status"] == "NO_ORDER"
    assert order["reason"] == "confidence_below_rr_unit_threshold"


def test_compatibility_marker_cannot_bypass_failed_risk():
    order = ProtectedSimulationOrderBuilder().build(
        {
            "action": "BUY",
            "confidence": 85,
            "risk": {"allowed": False},
            "execution_policy": "LEGACY_SIMULATION_COMPATIBILITY",
            "simulation_compatibility_units": 1,
        },
        {"symbol": "GOLD#", "closes": [2300, 2301], "spread": 18},
        balance=1000,
    )
    assert order["status"] == "NO_ORDER"


def test_spread_protection_stays_fail_closed():
    result = ConfidenceCalibrator().calibrate(_protected(spread=99), _modular(90), balance=1000)
    assert result["base"]["risk"]["allowed"] is False
    assert result["protected_order"]["status"] == "NO_ORDER"


def test_98_plus_uses_normal_confidence_unit_policy():
    result = ConfidenceCalibrator().calibrate(_protected(), _modular(98.6), balance=1000)
    order = result["protected_order"]
    assert order["status"] == "SIMULATION_ORDER_READY"
    assert order["unit_allocation"]["approved_units"] == 2
    assert order["unit_allocation"]["source"] == "CONFIDENCE_MAXIMUM_UNIT_POLICY"
