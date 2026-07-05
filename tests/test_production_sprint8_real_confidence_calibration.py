from afip.risk.confidence_calibrator import ConfidenceCalibrator


def test_confidence_calibration_turns_strong_modular_decision_into_risk_pass():
    protected = {
        "mode": "SIMULATION",
        "base": {
            "signal": {
                "snapshots": {
                    "H1": {
                        "symbol": "GOLD#",
                        "spread": 18,
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
    modular = {
        "decision": {
            "action": "BUY",
            "confidence": 85,
            "buy_score": 85,
            "sell_score": 0,
            "penalties": 0,
            "reason": "decision_intelligence_buy_edge",
        }
    }

    result = ConfidenceCalibrator().calibrate(protected, modular, balance=1000)

    assert result["confidence_calibration"]["status"] == "APPLIED"
    assert result["base"]["risk"]["allowed"] is True
    assert result["protected_order"]["status"] == "SIMULATION_ORDER_READY"
    assert result["protected_order"]["action"] == "BUY"


def test_confidence_calibration_keeps_spread_protection_locked():
    protected = {
        "mode": "SIMULATION",
        "base": {
            "signal": {
                "snapshots": {
                    "H1": {
                        "symbol": "GOLD#",
                        "spread": 99,
                        "closes": [2300.0, 2301.0, 2302.0],
                    }
                },
                "score": {"overall_confidence": 0, "risk_penalty": 0},
            }
        },
        "protected_order": {"status": "NO_ORDER"},
    }
    modular = {
        "decision": {
            "action": "BUY",
            "confidence": 90,
            "buy_score": 90,
            "sell_score": 0,
            "penalties": 0,
        }
    }

    result = ConfidenceCalibrator().calibrate(protected, modular, balance=1000)

    assert result["base"]["risk"]["allowed"] is False
    assert "spread_too_high" in result["base"]["risk"]["reasons"]
    assert result["protected_order"]["status"] == "NO_ORDER"
