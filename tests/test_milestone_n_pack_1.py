from afip.portfolio_intelligence_foundation import PortfolioIntelligenceFoundationRuntime


def _record():
    return {
        "knowledge_completion_id": "MCOMP-1234567890ABCDEF",
        "milestone_m_complete": True,
        "research_knowledge_approved": True,
        "production_knowledge_approved": False,
        "profiles": [
            {
                "profile_id": "PROFILE-1", "enabled": True,
                "equity": 1000.0, "margin_used": 50.0, "free_margin": 950.0,
                "risk_budget_percent": 1.0,
                "positions": [{"position_id": "POS-1"}],
            },
            {
                "profile_id": "PROFILE-2", "enabled": True,
                "equity": 500.0, "margin_used": 20.0, "free_margin": 480.0,
                "risk_budget_percent": 1.5,
                "positions": [],
            },
        ],
        "allowed_position_lifecycle": [
            "INDEPENDENT_TRADE_PLAN", "PROTECTED_RUNNER",
            "INDEPENDENT_POSITION_LIFECYCLE", "MULTI_DAY_POSITION_MANAGEMENT",
            "TRAILING_STOP", "PARTIAL_CLOSE", "DYNAMIC_STOP_LOSS", "DYNAMIC_TAKE_PROFIT",
        ],
        "disabled_methods": [
            "TRADITIONAL_DCA", "AVERAGING_DOWN", "MARTINGALE", "GRID_TRADING", "RECOVERY_TRADING",
        ],
        "data_quality_certified": True,
        "market_regime_before_signal": True,
        "deterministic_runtime_valid": True,
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
    }


def test_ready_portfolio_foundation():
    report = PortfolioIntelligenceFoundationRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.portfolio_intelligence_foundation_ready is True
    assert report.total_equity == 1500.0


def test_requires_milestone_m_lineage_and_research_approval():
    record = _record(); record["knowledge_completion_id"] = ""; record["research_knowledge_approved"] = False
    report = PortfolioIntelligenceFoundationRuntime().evaluate_one(record)
    assert "knowledge_completion_lineage_missing" in report.block_reasons
    assert "research_knowledge_not_approved" in report.block_reasons


def test_blocks_invalid_capital_and_duplicate_exposure():
    record = _record(); record["profiles"][0]["margin_used"] = 1200.0
    record["profiles"][1]["positions"] = [{"position_id": "POS-1"}]
    report = PortfolioIntelligenceFoundationRuntime().evaluate_one(record)
    assert "capital_snapshot_invalid" in report.block_reasons
    assert "exposure_snapshot_invalid" in report.block_reasons


def test_requires_independent_lifecycle_and_protected_runner():
    record = _record(); record["allowed_position_lifecycle"] = []
    report = PortfolioIntelligenceFoundationRuntime().evaluate_one(record)
    assert "independent_position_lifecycle_missing" in report.block_reasons
    assert "protected_runner_policy_missing" in report.block_reasons


def test_forbidden_methods_must_remain_disabled():
    record = _record(); record["disabled_methods"].remove("MARTINGALE")
    report = PortfolioIntelligenceFoundationRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert "forbidden_portfolio_method_enabled" in report.block_reasons


def test_deterministic_identity_and_feature_locks():
    a = PortfolioIntelligenceFoundationRuntime().evaluate_one(_record())
    record = _record(); record["profiles"] = list(reversed(record["profiles"]))
    b = PortfolioIntelligenceFoundationRuntime().evaluate_one(record)
    assert a.foundation_id == b.foundation_id
    assert a.adaptive_position_sizing_enabled is False
    assert a.portfolio_risk_engine_enabled is False
    assert a.capital_allocation_enabled is False


def test_permanent_execution_lock_and_serializable_payload():
    record = _record(); record["direct_execution"] = True; record["order_transmission_attempted"] = True
    report = PortfolioIntelligenceFoundationRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    payload = report.as_dict()
    assert payload["feature_flags"]["live_execution_enabled"] is False
    assert payload["trading_logic_changed"] is False
