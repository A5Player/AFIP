from afip.portfolio_resilience_certification import PortfolioResilienceCertificationRuntime


def _record():
    return {
        "allocation_id": "CA-001",
        "coordination_id": "PEC-001",
        "protection_id": "PDP-001",
        "stress_validation_id": "PSV-001",
        "profile_id": "PROFILE-1",
        "market_regime": "TRENDING",
        "capital_allocation_approved": True,
        "capital_allocation_ready": True,
        "portfolio_exposure_approved": True,
        "portfolio_exposure_coordination_ready": True,
        "portfolio_drawdown_protection_approved": True,
        "portfolio_drawdown_protection_ready": True,
        "portfolio_stress_validation_approved": True,
        "portfolio_stress_validation_ready": True,
        "data_quality_certified": True,
        "market_regime_before_signal": True,
        "independent_position_lifecycles_valid": True,
        "protected_runner_preserved": True,
        "traditional_dca_disabled": True,
        "averaging_down_disabled": True,
        "martingale_disabled": True,
        "grid_trading_disabled": True,
        "recovery_trading_disabled": True,
        "broker": "XM",
        "symbol": "GOLD#",
        "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT",
    }


def test_ready_report_certifies_complete_resilience_lineage():
    report = PortfolioResilienceCertificationRuntime().evaluate(_record())
    assert report.status == "READY"
    assert report.portfolio_resilience_certified is True
    assert report.production_knowledge_approved is True


def test_report_is_deterministic():
    runtime = PortfolioResilienceCertificationRuntime()
    assert runtime.evaluate(_record()) == runtime.evaluate(dict(reversed(list(_record().items()))))


def test_blocks_missing_stress_validation_lineage():
    record = _record(); record["stress_validation_id"] = ""
    report = PortfolioResilienceCertificationRuntime().evaluate(record)
    assert "stress_validation_lineage_missing" in report.block_reasons


def test_blocks_unapproved_drawdown_protection():
    record = _record(); record["portfolio_drawdown_protection_approved"] = False
    report = PortfolioResilienceCertificationRuntime().evaluate(record)
    assert "portfolio_drawdown_protection_not_approved" in report.block_reasons


def test_blocks_future_leakage():
    record = _record(); record["future_leakage_detected"] = True
    report = PortfolioResilienceCertificationRuntime().evaluate(record)
    assert "future_leakage_detected" in report.block_reasons


def test_blocks_forbidden_method_enablement():
    record = _record(); record["martingale_disabled"] = False
    report = PortfolioResilienceCertificationRuntime().evaluate(record)
    assert "forbidden_trading_method_enabled" in report.block_reasons


def test_execution_safety_is_permanently_locked():
    record = _record(); record["direct_execution"] = True
    report = PortfolioResilienceCertificationRuntime().evaluate(record)
    assert report.status == "BLOCKED"
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"


def test_locked_policy_metadata_remains_unchanged():
    report = PortfolioResilienceCertificationRuntime().evaluate(_record())
    assert (report.broker, report.symbol, report.base_lot_per_unit) == ("XM", "GOLD#", 0.01)
    assert report.research_only is True
    assert report.trading_logic_changed is False
