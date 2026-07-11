from afip.portfolio_exposure_coordination import PortfolioExposureCoordinationRuntime


def record(**overrides):
    value = {
        "allocation_id": "CA-001",
        "risk_evaluation_id": "PRE-001",
        "profile_id": "profile-1",
        "market_regime": "TREND",
        "maximum_portfolio_units": 3,
        "maximum_portfolio_risk_amount": 30.0,
        "maximum_protected_runner_units": 1,
        "maximum_direction_concentration_percent": 100.0,
        "capital_allocation_approved": True,
        "capital_allocation_ready": True,
        "data_quality_certified": True,
    }
    value.update(overrides)
    return value


def allocations():
    return [
        {"trade_plan_id": "TP-1", "direction": "BUY", "allocated_units": 1, "allocated_risk_amount": 10.0, "protected_runner": True, "independent_position_lifecycle": True},
        {"trade_plan_id": "TP-2", "direction": "BUY", "allocated_units": 1, "allocated_risk_amount": 8.0, "protected_runner": False, "independent_position_lifecycle": True},
    ]


def test_ready_report_coordinates_allocated_exposure():
    report = PortfolioExposureCoordinationRuntime().evaluate(record(), allocations())
    assert report.status == "READY"
    assert report.portfolio_exposure_coordination_ready is True
    assert report.total_units == 2
    assert report.total_risk_amount == 18.0


def test_report_is_deterministic():
    runtime = PortfolioExposureCoordinationRuntime()
    first = runtime.evaluate(record(), allocations())
    second = runtime.evaluate(record(), reversed(allocations()))
    assert first.coordination_id == second.coordination_id
    assert first.as_dict() == second.as_dict()


def test_blocks_direction_concentration_limit():
    report = PortfolioExposureCoordinationRuntime().evaluate(
        record(maximum_direction_concentration_percent=60.0), allocations()
    )
    assert report.status == "BLOCKED"
    assert "direction_concentration_limit_exceeded" in report.block_reasons


def test_blocks_protected_runner_limit():
    plans = allocations()
    plans[1]["protected_runner"] = True
    report = PortfolioExposureCoordinationRuntime().evaluate(record(), plans)
    assert "protected_runner_limit_exceeded" in report.block_reasons


def test_blocks_duplicate_trade_plan_lineage():
    plans = allocations()
    plans[1]["trade_plan_id"] = "TP-1"
    report = PortfolioExposureCoordinationRuntime().evaluate(record(), plans)
    assert "trade_plan_lineage_invalid" in report.block_reasons


def test_blocks_forbidden_method_enablement():
    report = PortfolioExposureCoordinationRuntime().evaluate(
        record(martingale_disabled=False), allocations()
    )
    assert "forbidden_trading_method_enabled" in report.block_reasons


def test_execution_safety_is_permanently_locked():
    report = PortfolioExposureCoordinationRuntime().evaluate(
        record(direct_execution=True, order_status="ORDER_SENT"), allocations()
    )
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.order_status == "NO_ORDER_SENT"
    assert "execution_enablement_forbidden" in report.block_reasons
    assert "order_status_invalid" in report.block_reasons


def test_locked_policy_metadata_remains_unchanged():
    report = PortfolioExposureCoordinationRuntime().evaluate(record(), allocations())
    assert report.broker == "XM"
    assert report.symbol == "GOLD#"
    assert report.base_lot_per_unit == 0.01
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.research_only is True
    assert report.production_knowledge_approved is False
    assert report.trading_logic_changed is False
