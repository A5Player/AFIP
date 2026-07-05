from afip.engine.decision_engine_v2 import DecisionEngineV2
from afip.engine.institutional_score_engine import InstitutionalScoreEngine
from afip.engine.signal_quality_engine import SignalQualityEngine


def _intelligence(direction="BUY", confidence=82):
    return [
        {"name": "FairValueGapIntelligence", "direction": direction, "confidence": confidence},
        {"name": "ImbalanceIntelligence", "direction": direction, "confidence": confidence - 5},
        {"name": "OrderBlockIntelligence", "direction": direction, "confidence": confidence + 2},
        {"name": "LiquiditySweepIntelligence", "direction": "FLAT", "confidence": 44},
        {"name": "SmartMoneyConceptIntelligence", "direction": direction, "confidence": confidence + 4},
    ]


def test_institutional_score_engine_buy_bias():
    result = InstitutionalScoreEngine().evaluate({"intelligence": _intelligence("BUY", 80)})
    assert result["status"] == "READY"
    assert result["action"] == "BUY"
    assert result["buy_score"] > result["sell_score"]


def test_signal_quality_engine_ready():
    result = SignalQualityEngine().evaluate({
        "closes": [100, 101, 102, 103, 104, 105],
        "highs": [101, 102, 103, 104, 105, 106],
        "lows": [99, 100, 101, 102, 103, 104],
    })
    assert result["status"] == "READY"
    assert result["action"] in {"BUY", "WAIT"}
    assert result["confidence"] >= 50


def test_decision_engine_v2_returns_production_payload():
    result = DecisionEngineV2().evaluate({
        "intelligence": _intelligence("BUY", 84),
        "trading_cost": {"spread_points": 20, "max_spread_points": 35},
        "drawdown_percent": 1.5,
        "equity": 1000,
        "risk_percent": 0.6,
        "stop_points": 900,
        "point_value_per_lot": 0.01,
        "closes": [100, 101, 102, 103, 104, 105],
        "highs": [101, 102, 103, 104, 105, 106],
        "lows": [99, 100, 101, 102, 103, 104],
    })
    assert result["name"] == "DecisionEngineV2"
    assert result["status"] in {"READY", "CAUTION"}
    assert "institutional" in result
    assert "execution_readiness" in result
