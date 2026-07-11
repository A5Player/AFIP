from afip.adaptive_position_sizing import AdaptivePositionSizingRuntime


def _record():
    return {
        "foundation_id": "NPF-1234567890ABCDEF",
        "portfolio_intelligence_foundation_ready": True,
        "profile_id": "PROFILE-1",
        "market_regime": "TRENDING_BULLISH",
        "equity": 3000.0,
        "free_margin": 2800.0,
        "risk_budget_percent": 1.0,
        "stop_distance_points": 100.0,
        "value_per_point_per_unit": 0.1,
        "confidence_score": 95.0,
        "minimum_capital_per_unit": 1000.0,
        "margin_required_per_unit": 100.0,
        "maximum_units": 3,
        "base_lot_per_unit": 0.01,
        "market_regime_before_signal": True,
        "independent_trade_plan_required": True,
        "protected_runner_supported": True,
        "data_quality_certified": True,
        "broker": "XM", "symbol": "GOLD#",
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
    }


def test_ready_adaptive_position_sizing():
    report = AdaptivePositionSizingRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.recommended_units == 3
    assert report.recommended_lot == 0.03


def test_confidence_reduces_or_blocks_units():
    medium = _record(); medium["confidence_score"] = 75.0
    low = _record(); low["confidence_score"] = 59.0
    a = AdaptivePositionSizingRuntime().evaluate_one(medium)
    b = AdaptivePositionSizingRuntime().evaluate_one(low)
    assert a.recommended_units < 3
    assert b.status == "BLOCKED"
    assert b.recommended_units == 0


def test_capital_and_margin_caps_are_enforced():
    record = _record(); record["equity"] = 1500.0; record["free_margin"] = 150.0
    report = AdaptivePositionSizingRuntime().evaluate_one(record)
    assert report.capital_limit_units == 1
    assert report.margin_limit_units == 1
    assert report.recommended_units == 1


def test_invalid_risk_or_stop_blocks_sizing():
    record = _record(); record["risk_budget_percent"] = 8.0; record["stop_distance_points"] = 0.0
    report = AdaptivePositionSizingRuntime().evaluate_one(record)
    assert "risk_budget_invalid" in report.block_reasons
    assert "stop_distance_or_value_invalid" in report.block_reasons
    assert report.recommended_units == 0


def test_requires_foundation_regime_and_data_quality():
    record = _record(); record["foundation_id"] = ""; record["market_regime"] = ""; record["data_quality_certified"] = False
    report = AdaptivePositionSizingRuntime().evaluate_one(record)
    assert "portfolio_foundation_lineage_missing" in report.block_reasons
    assert "market_regime_sequence_invalid" in report.block_reasons
    assert "data_quality_not_certified" in report.block_reasons


def test_deterministic_identity_and_permanent_caps():
    a = AdaptivePositionSizingRuntime().evaluate_one(_record())
    b = AdaptivePositionSizingRuntime().evaluate_one(dict(reversed(list(_record().items()))))
    assert a.sizing_id == b.sizing_id
    record = _record(); record["maximum_units"] = 4
    blocked = AdaptivePositionSizingRuntime().evaluate_one(record)
    assert "maximum_units_policy_violation" in blocked.block_reasons


def test_execution_remains_locked_and_payload_serializes():
    record = _record(); record["direct_execution"] = True; record["broker_request_created"] = True
    report = AdaptivePositionSizingRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.production_knowledge_approved is False
    assert report.as_dict()["trading_logic_changed"] is False
