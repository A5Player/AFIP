from afip.portfolio_drawdown_protection import PortfolioDrawdownProtectionRuntime

def record(**overrides):
    data = {
        "coordination_id": "PEC-001", "allocation_id": "CA-001", "profile_id": "PROFILE-1", "market_regime": "TRENDING",
        "starting_equity": 1000.0, "current_equity": 970.0, "peak_equity": 1020.0, "equity_floor": 900.0,
        "maximum_drawdown_percent": 10.0, "daily_loss_amount": 20.0, "maximum_daily_loss_amount": 40.0,
        "consecutive_loss_count": 2, "maximum_consecutive_losses": 3,
        "portfolio_exposure_approved": True, "portfolio_exposure_coordination_ready": True,
        "independent_position_lifecycles_valid": True, "protected_runner_exposure_included": True,
        "market_regime_before_signal": True, "data_quality_certified": True,
    }
    data.update(overrides)
    return data

def test_ready_report_protects_portfolio_drawdown():
    report = PortfolioDrawdownProtectionRuntime().evaluate(record())
    assert report.status == "READY"
    assert report.portfolio_drawdown_protection_approved is True
    assert report.drawdown_percent == round(50 / 1020 * 100, 8)

def test_report_is_deterministic():
    runtime = PortfolioDrawdownProtectionRuntime()
    assert runtime.evaluate(record()).as_dict() == runtime.evaluate(record()).as_dict()

def test_blocks_equity_floor_breach():
    report = PortfolioDrawdownProtectionRuntime().evaluate(record(current_equity=890.0))
    assert "equity_floor_breached" in report.block_reasons
    assert report.reduce_new_allocation_required is True

def test_blocks_maximum_drawdown_breach():
    report = PortfolioDrawdownProtectionRuntime().evaluate(record(current_equity=850.0, equity_floor=800.0))
    assert "maximum_drawdown_exceeded" in report.block_reasons

def test_blocks_daily_loss_limit():
    report = PortfolioDrawdownProtectionRuntime().evaluate(record(daily_loss_amount=50.0))
    assert "maximum_daily_loss_exceeded" in report.block_reasons

def test_blocks_consecutive_loss_limit():
    report = PortfolioDrawdownProtectionRuntime().evaluate(record(consecutive_loss_count=4))
    assert "maximum_consecutive_losses_exceeded" in report.block_reasons

def test_forbidden_methods_and_execution_remain_locked():
    report = PortfolioDrawdownProtectionRuntime().evaluate(record(martingale_disabled=False, direct_execution=True, order_status="ORDER_SENT"))
    assert "forbidden_trading_method_enabled" in report.block_reasons
    assert "execution_enablement_forbidden" in report.block_reasons
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"

def test_locked_policy_metadata_remains_unchanged():
    report = PortfolioDrawdownProtectionRuntime().evaluate(record())
    assert (report.broker, report.symbol, report.base_lot_per_unit) == ("XM", "GOLD#", 0.01)
    assert report.research_only is True
    assert report.production_knowledge_approved is False
    assert report.preserve_existing_protected_runner is True
    assert report.trading_logic_changed is False
