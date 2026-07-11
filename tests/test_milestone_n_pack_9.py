from afip.portfolio_governance_validation import PortfolioGovernanceValidationRuntime


def _record():
    return {
        "certification_id": "PRC-ABC123",
        "profile_id": "PROFILE-1",
        "policy_version": "AFIP_V1.0_FEATURE_FREEZE",
        "configuration_hash": "cfg-001",
        "audit_reference": "audit-001",
        "portfolio_resilience_certified": True,
        "portfolio_resilience_ready": True,
        "configuration_integrity_valid": True,
        "audit_lineage_complete": True,
        "authority_separation_valid": True,
        "independent_position_lifecycles_valid": True,
        "protected_runner_preserved": True,
    }


def test_ready_report_validates_portfolio_governance():
    report = PortfolioGovernanceValidationRuntime().evaluate(_record())
    assert report.status == "READY"
    assert report.portfolio_governance_approved is True
    assert report.portfolio_governance_ready is True


def test_report_is_deterministic():
    runtime = PortfolioGovernanceValidationRuntime()
    assert runtime.evaluate(_record()).governance_id == runtime.evaluate(_record()).governance_id


def test_blocks_invalid_policy_version():
    record = _record(); record["policy_version"] = "UNLOCKED"
    report = PortfolioGovernanceValidationRuntime().evaluate(record)
    assert "feature_freeze_policy_invalid" in report.block_reasons


def test_blocks_configuration_integrity_failure():
    record = _record(); record["configuration_integrity_valid"] = False
    report = PortfolioGovernanceValidationRuntime().evaluate(record)
    assert "configuration_integrity_invalid" in report.block_reasons


def test_blocks_incomplete_audit_lineage():
    record = _record(); record["audit_lineage_complete"] = False
    report = PortfolioGovernanceValidationRuntime().evaluate(record)
    assert "audit_lineage_incomplete" in report.block_reasons


def test_blocks_manual_execution_override():
    record = _record(); record["manual_execution_override"] = True
    report = PortfolioGovernanceValidationRuntime().evaluate(record)
    assert "manual_execution_override_forbidden" in report.block_reasons


def test_blocks_forbidden_method_enablement():
    record = _record(); record["martingale_disabled"] = False
    report = PortfolioGovernanceValidationRuntime().evaluate(record)
    assert "forbidden_trading_method_enabled" in report.block_reasons


def test_execution_safety_is_permanently_locked():
    report = PortfolioGovernanceValidationRuntime().evaluate(_record())
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.order_status == "NO_ORDER_SENT"
    assert report.broker_request_created is False
    assert report.order_transmission_attempted is False
    assert report.position_modification_attempted is False
    assert report.trading_logic_changed is False
