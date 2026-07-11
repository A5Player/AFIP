from afip.portfolio_intelligence_complete import PortfolioIntelligenceCompleteRuntime


_CAPABILITIES = (
    "portfolio_intelligence_foundation",
    "adaptive_position_sizing",
    "portfolio_risk_engine",
    "capital_allocation",
    "portfolio_exposure_coordination",
    "portfolio_drawdown_protection",
    "portfolio_stress_validation",
    "portfolio_resilience_certification",
    "portfolio_governance_validation",
)


def _record():
    return {
        "portfolio_version": "N1.10.0-RESEARCH",
        "governance_id": "PGV-ABC123",
        "capabilities": {name: True for name in _CAPABILITIES},
        "capability_lineages": [f"N-{index}" for index in range(1, 10)],
        "portfolio_governance_approved": True,
        "portfolio_governance_ready": True,
        "data_quality_certified": True,
        "deterministic_runtime_valid": True,
        "market_regime_before_signal": True,
        "independent_trade_plans_valid": True,
        "independent_position_lifecycles_valid": True,
        "protected_runner_preserved": True,
        "broker": "XM",
        "symbol": "GOLD#",
        "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT",
    }


def test_ready_report_closes_milestone_n_without_production_certification():
    report = PortfolioIntelligenceCompleteRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.milestone_n_complete is True
    assert report.ready_for_milestone_o is True
    assert report.production_certified is False
    assert report.research_only is True


def test_completion_identity_is_deterministic():
    runtime = PortfolioIntelligenceCompleteRuntime()
    first = runtime.evaluate_one(_record())
    record = _record(); record["capability_lineages"] = list(reversed(record["capability_lineages"]))
    second = runtime.evaluate_one(record)
    assert first.completion_id == second.completion_id


def test_requires_every_portfolio_capability():
    record = _record(); record["capabilities"]["portfolio_governance_validation"] = False
    report = PortfolioIntelligenceCompleteRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert "portfolio_governance_validation" in report.missing_capabilities


def test_requires_governance_and_unique_lineage():
    record = _record(); record["governance_id"] = ""; record["capability_lineages"] = ["N-1"] * 9
    report = PortfolioIntelligenceCompleteRuntime().evaluate_one(record)
    assert "portfolio_governance_not_approved" in report.block_reasons
    assert "capability_lineage_invalid" in report.block_reasons


def test_requires_data_integrity_determinism_and_regime_sequence():
    record = _record()
    record["data_quality_certified"] = False
    record["future_leakage_detected"] = True
    record["deterministic_runtime_valid"] = False
    record["market_regime_before_signal"] = False
    report = PortfolioIntelligenceCompleteRuntime().evaluate_one(record)
    assert "data_quality_not_certified" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons
    assert "deterministic_runtime_invalid" in report.block_reasons
    assert "market_regime_sequence_invalid" in report.block_reasons


def test_requires_independent_lifecycles_and_runner_preservation():
    record = _record()
    record["independent_trade_plans_valid"] = False
    record["independent_position_lifecycles_valid"] = False
    record["protected_runner_preserved"] = False
    report = PortfolioIntelligenceCompleteRuntime().evaluate_one(record)
    assert "independent_trade_plan_required" in report.block_reasons
    assert "independent_position_lifecycle_required" in report.block_reasons
    assert "protected_runner_preservation_required" in report.block_reasons


def test_forbidden_methods_and_permanent_policy_are_enforced():
    record = _record()
    record["martingale_disabled"] = False
    record["broker"] = "OTHER"
    record["base_lot_per_unit"] = 0.02
    report = PortfolioIntelligenceCompleteRuntime().evaluate_one(record)
    assert "forbidden_trading_method_enabled" in report.block_reasons
    assert "broker_policy_violation" in report.block_reasons
    assert "base_unit_policy_violation" in report.block_reasons


def test_execution_and_trading_logic_remain_permanently_locked():
    record = _record()
    record["live_execution_enabled"] = True
    record["order_transmission_attempted"] = True
    record["position_modification_attempted"] = True
    record["trading_logic_changed"] = True
    report = PortfolioIntelligenceCompleteRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.order_status == "NO_ORDER_SENT"
    assert "execution_enablement_forbidden" in report.block_reasons
    assert "order_transmission_forbidden" in report.block_reasons
    assert "position_modification_forbidden" in report.block_reasons
    assert "trading_logic_change_forbidden" in report.block_reasons
