from afip.order_evidence_dashboard import build_order_evidence, render_order_evidence_dashboard


def test_historical_order_sent_is_not_current_order_sent_when_runtime_stopped():
    evidence = build_order_evidence({
        "profile_id": "P1",
        "runtime_state": "STOPPED",
        "order_status": "ORDER_SENT",
        "gateway_reason": "protected_demo_orders_sent",
        "runtime_truth": {
            "runtime_current": "STOPPED",
            "gateway_current": "INACTIVE",
            "current_reason": "runtime_not_currently_running",
            "last_gateway_event": "ORDER_SENT",
            "last_gateway_event_age_seconds": 100,
        },
    })
    assert evidence["current_order_status"] == "NO_CURRENT_ORDER"
    assert evidence["current_permission"] == "NOT_EVALUATED_RUNTIME_STOPPED"
    assert evidence["historical_status"] == "ORDER_SENT"
    assert evidence["historical_reason"] == "protected_demo_orders_sent"


def test_market_closed_current_truth_is_separate_from_blocked_history():
    evidence = build_order_evidence({
        "profile_id": "P4",
        "market_status": "CLOSED_WEEKEND",
        "runtime_state": "RUNNING",
        "order_status": "BLOCKED",
        "gateway_reason": "capital_tier_lot_out_of_range",
        "runtime_truth": {
            "runtime_current": "RUNNING",
            "gateway_current": "INACTIVE",
            "current_reason": "market_closed_no_new_execution_expected",
        },
    })
    assert evidence["current_order_status"] == "NO_CURRENT_ORDER"
    assert evidence["current_permission"] == "MARKET_CLOSED"
    assert evidence["historical_status"] == "BLOCKED"


def test_render_labels_current_and_historical_sections():
    evidence = build_order_evidence({
        "profile_id": "P2",
        "runtime_state": "STOPPED",
        "order_status": "BLOCKED",
        "gateway_reason": "execution_ownership_mismatch_before_order_check",
    })
    html = render_order_evidence_dashboard({"order_evidence": [evidence]})
    assert "Current Runtime Truth" in html
    assert "Last Historical Evidence" in html
    assert "Current reason" in html
    assert "Historical reason" in html
    assert "current runtime state never inherits ORDER_SENT or BLOCKED" in html
