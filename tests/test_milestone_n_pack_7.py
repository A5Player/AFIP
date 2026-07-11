from afip.portfolio_stress_validation import PortfolioStressValidationRuntime


def record(**overrides):
    data = {
        "protection_id": "PDP-001",
        "coordination_id": "PEC-001",
        "allocation_id": "CA-001",
        "profile_id": "PROFILE-1",
        "market_regime": "TRENDING",
        "current_equity": 1000.0,
        "equity_floor": 850.0,
        "allocated_risk_amount": 30.0,
        "spread_cost_shock_amount": 10.0,
        "volatility_shock_amount": 20.0,
        "adverse_movement_amount": 25.0,
        "liquidity_buffer_amount": 35.0,
        "maximum_stressed_drawdown_percent": 10.0,
        "portfolio_drawdown_protection_approved": True,
        "portfolio_drawdown_protection_ready": True,
        "portfolio_exposure_approved": True,
        "portfolio_exposure_coordination_ready": True,
        "capital_allocation_approved": True,
        "capital_allocation_ready": True,
        "independent_position_lifecycles_valid": True,
        "protected_runner_preserved": True,
        "market_regime_before_signal": True,
        "data_quality_certified": True,
    }
    data.update(overrides)
    return data


def test_ready_report_validates_portfolio_stress():
    report = PortfolioStressValidationRuntime().evaluate(record())
    assert report.status == "READY"
    assert report.portfolio_stress_validation_approved is True
    assert report.total_stress_loss_amount == 85.0
    assert report.stressed_equity == 915.0


def test_report_is_deterministic():
    runtime = PortfolioStressValidationRuntime()
    assert runtime.evaluate(record()).as_dict() == runtime.evaluate(record()).as_dict()


def test_blocks_stressed_equity_floor_breach():
    report = PortfolioStressValidationRuntime().evaluate(record(equity_floor=930.0))
    assert "stressed_equity_floor_breached" in report.block_reasons
    assert report.new_allocation_permitted_for_research is False


def test_blocks_stressed_drawdown_limit():
    report = PortfolioStressValidationRuntime().evaluate(record(maximum_stressed_drawdown_percent=5.0))
    assert "maximum_stressed_drawdown_exceeded" in report.block_reasons


def test_blocks_insufficient_liquidity_buffer():
    report = PortfolioStressValidationRuntime().evaluate(record(liquidity_buffer_amount=25.0))
    assert "liquidity_buffer_insufficient" in report.block_reasons


def test_requires_pack_4_to_pack_6_lineage_approval():
    report = PortfolioStressValidationRuntime().evaluate(record(portfolio_drawdown_protection_ready=False, capital_allocation_ready=False))
    assert "portfolio_drawdown_protection_not_approved" in report.block_reasons
    assert "capital_allocation_not_approved" in report.block_reasons


def test_forbidden_methods_and_execution_remain_locked():
    report = PortfolioStressValidationRuntime().evaluate(record(grid_trading_disabled=False, live_execution_enabled=True, position_modification_attempted=True))
    assert "forbidden_trading_method_enabled" in report.block_reasons
    assert "execution_enablement_forbidden" in report.block_reasons
    assert "position_modification_forbidden" in report.block_reasons
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"


def test_locked_policy_metadata_remains_unchanged():
    report = PortfolioStressValidationRuntime().evaluate(record())
    assert (report.broker, report.symbol, report.base_lot_per_unit) == ("XM", "GOLD#", 0.01)
    assert report.research_only is True
    assert report.production_knowledge_approved is False
    assert report.trading_logic_changed is False
