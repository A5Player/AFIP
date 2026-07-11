from afip.capital_allocation import CapitalAllocationRuntime


def _record():
    return {
        "risk_evaluation_id": "PRE-1234567890ABCDEF", "portfolio_risk_approved": True,
        "portfolio_risk_engine_ready": True, "profile_id": "PROFILE-1",
        "market_regime": "TRENDING_BULLISH", "equity": 3000.0, "free_margin": 2500.0,
        "minimum_free_margin_reserve": 500.0, "current_open_risk_amount": 20.0,
        "maximum_portfolio_risk_percent": 3.0, "current_units": 1,
        "maximum_portfolio_units": 3, "base_lot_per_unit": 0.01,
        "market_regime_before_signal": True, "protected_runner_exposure_included": True,
        "traditional_dca_disabled": True, "averaging_down_disabled": True,
        "martingale_disabled": True, "grid_trading_disabled": True,
        "recovery_trading_disabled": True, "data_quality_certified": True,
        "broker": "XM", "symbol": "GOLD#", "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT",
    }


def _plans():
    return [
        {"trade_plan_id": "TP-B", "priority_score": 80, "requested_units": 2,
         "risk_amount_per_unit": 25.0, "margin_required_per_unit": 300.0,
         "independent_position_lifecycle": True},
        {"trade_plan_id": "TP-A", "priority_score": 95, "requested_units": 1,
         "risk_amount_per_unit": 20.0, "margin_required_per_unit": 250.0,
         "protected_runner": True, "independent_position_lifecycle": True},
    ]


def test_ready_allocation_uses_priority_and_capacity():
    report = CapitalAllocationRuntime().evaluate(_record(), _plans())
    assert report.status == "READY"
    assert report.allocated_units == 2
    assert report.rejected_units == 1
    assert report.allocations[0].trade_plan_id == "TP-A"
    assert report.allocations[0].allocated_units == 1
    assert report.allocations[1].allocated_units == 1
    assert report.allocated_risk_amount == 45.0


def test_risk_capacity_can_limit_units_before_unit_ceiling():
    record = _record(); record["current_open_risk_amount"] = 65.0
    report = CapitalAllocationRuntime().evaluate(record, _plans())
    assert report.allocated_units == 1
    assert report.allocations[0].trade_plan_id == "TP-A"
    assert report.remaining_risk_amount == 5.0


def test_margin_reserve_is_preserved():
    record = _record(); record["free_margin"] = 900.0; record["minimum_free_margin_reserve"] = 500.0
    report = CapitalAllocationRuntime().evaluate(record, _plans())
    assert report.allocated_units == 1
    assert report.remaining_margin_amount == 150.0


def test_invalid_lineage_and_lifecycle_block_allocation():
    plans = _plans(); plans[1]["trade_plan_id"] = "TP-B"; plans[0]["independent_position_lifecycle"] = False
    report = CapitalAllocationRuntime().evaluate(_record(), plans)
    assert report.status == "BLOCKED"
    assert report.allocated_units == 0
    assert "trade_plan_lineage_invalid" in report.block_reasons
    assert "independent_position_lifecycle_required" in report.block_reasons


def test_forbidden_method_or_missing_runner_exposure_blocks():
    record = _record(); record["martingale_disabled"] = False; record["protected_runner_exposure_included"] = False
    report = CapitalAllocationRuntime().evaluate(record, _plans())
    assert "forbidden_trading_method_enabled" in report.block_reasons
    assert "protected_runner_exposure_missing" in report.block_reasons


def test_no_capacity_is_explicitly_blocked():
    record = _record(); record["current_units"] = 3
    report = CapitalAllocationRuntime().evaluate(record, _plans())
    assert report.status == "BLOCKED"
    assert "no_allocatable_portfolio_capacity" in report.block_reasons


def test_deterministic_identity_is_input_order_independent():
    plans = _plans()
    a = CapitalAllocationRuntime().evaluate(_record(), plans)
    b = CapitalAllocationRuntime().evaluate(dict(reversed(list(_record().items()))), reversed(plans))
    assert a.allocation_id == b.allocation_id


def test_execution_remains_locked_and_serializes():
    record = _record(); record["direct_execution"] = True; record["broker_request_created"] = True
    report = CapitalAllocationRuntime().evaluate(record, _plans())
    assert report.status == "BLOCKED"
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.as_dict()["trading_logic_changed"] is False
