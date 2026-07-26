from afip.dashboard_operations_health import assess_profile_operations, attach_operations_health


def profile(runtime="STOPPED", mt5="CONNECTED", market="CLOSED_WEEKEND"):
    return {
        "profile_id": "P1",
        "balance": 90.0,
        "equity": 90.0,
        "free_margin": 90.0,
        "bid": 4052.54,
        "ask": 4053.30,
        "runtime_truth": {
            "runtime_current": runtime,
            "mt5_current": mt5,
            "market_current": market,
            "gateway_current": "INACTIVE",
            "execution_authority_current": "LOCKED_SIMULATION_ONLY",
        },
    }


def test_connected_stopped_profile_is_monitoring_only_not_failed():
    result = assess_profile_operations(profile())
    assert result["overall_status"] == "IDLE_READY"
    assert result["operating_mode"] == "MONITORING_ONLY"
    assert result["financial_status"] == "READY"


def test_absent_financial_collectors_are_explicit_not_zero():
    result = assess_profile_operations(profile())
    assert result["today_realized_pl_status"] == "NOT_COLLECTED"
    assert result["cash_flow_status"] == "NOT_TRACKED"
    assert result["reserve_status"] == "NOT_CONFIGURED"
    assert result["available_allocation_status"] == "NOT_EVALUATED_RUNTIME_STOPPED"


def test_market_closed_decision_semantic_is_explicit():
    result = assess_profile_operations(profile())
    assert result["decision_evidence_status"] == "NOT_EVALUATED_MARKET_CLOSED"


def test_contract_summary_reports_monitoring_only():
    payload = attach_operations_health({"profiles": [profile() for _ in range(4)]})
    assert payload["operations_health_summary"]["status"] == "MONITORING_ONLY"
    assert payload["operations_health_summary"]["mt5_connected_profiles"] == 4
    assert payload["operations_health_summary"]["monitoring_only_profiles"] == 4
