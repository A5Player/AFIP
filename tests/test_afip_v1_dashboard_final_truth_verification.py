from afip.dashboard_truth_verification import attach_dashboard_truth_verification
from afip.dashboard_state_machine import normalize_profile_state
from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime


def _base_profile():
    return {
        "profile_id": "P1",
        "connection_status": "CONNECTED",
        "evidence_kind": "LIVE",
        "balance": 100.0,
        "equity": 101.0,
        "free_margin": 95.0,
        "bid": 4000.0,
        "ask": 4000.3,
        "financial_live": True,
        "runtime_state": "RUNNING",
        "source_metadata": {
            "live_mt5_snapshot": {"readable": True, "fresh": True, "path": "runtime/profiles/p1/mt5_live_snapshot.json", "age_seconds": 1},
            "execution_state": {
                "exists": True,
                "fresh": True,
                "modified_at_utc": "2026-07-28T10:00:00+00:00",
                "authority_data": {"execution": "DEMO_EXECUTION_ONLY"},
            },
            "profile_status": {"fresh": True, "exists": True},
            "mt5_health": {"fresh": True, "exists": True},
            "runtime_authority": {"fresh": True},
        },
    }


def test_live_snapshot_is_verified_only_when_complete_fresh_and_connected():
    contract = attach_dashboard_truth_verification({"profiles": [_base_profile()]})
    row = contract["profiles"][0]
    assert row["financial_snapshot_verified"] is True
    assert row["snapshot_verification"]["status"] == "VERIFIED"


def test_demo_authority_comes_from_execution_state_not_stale_health_alias():
    profile = _base_profile()
    profile["execution"] = "LOCKED_SIMULATION_ONLY"
    contract = attach_dashboard_truth_verification({"profiles": [profile]})
    row = contract["profiles"][0]
    assert row["execution_authority_current"] == "DEMO_EXECUTION_ONLY"
    truth = normalize_profile_state(row)
    assert truth["execution_authority_current"] == "DEMO_EXECUTION_ONLY"


def test_accepted_ticket_without_open_position_is_historical_not_active_position():
    profile = _base_profile()
    profile["source_metadata"]["execution_state"]["authority_data"].update({
        "order_status": "DEMO_ORDER_SENT",
        "sent_units": 1,
        "order_send_called": True,
        "order_check_called": True,
        "mt5_result_code": 10009,
        "tickets": [12345],
        "plan_id": "PLAN-1",
    })
    profile.update({"positions_total": 0, "position_tickets": [], "current_tickets": []})
    row = attach_dashboard_truth_verification({"profiles": [profile]})["profiles"][0]
    assert row["order_lifecycle"]["state"] == "ORDER_ACCEPTED_POSITION_NOT_OPEN"
    assert row["normalized_order_status"] == "LAST_ORDER_ACCEPTED"
    assert row["ticket_plan_lineage"]["status"] == "HISTORICAL_ORDER_ONLY"


def test_open_unmatched_position_is_explicit_warning_not_fake_plan_match():
    profile = _base_profile()
    profile.update({"positions_total": 1, "has_open_position": True, "position_tickets": [999], "current_tickets": [999]})
    row = attach_dashboard_truth_verification({"profiles": [profile]})["profiles"][0]
    assert row["order_lifecycle"]["state"] == "POSITION_OPEN_UNMATCHED"
    assert row["ticket_plan_lineage"]["status"] == "UNMATCHED_LIVE_POSITION"
    assert row["dashboard_consistency"]["status"] == "WARNING"


def test_dashboard_renders_truth_verification_fields():
    profile = _base_profile()
    html = ThreeDashboardRuntime().render_profiles_html({"profiles": [profile] * 4, "project_root": "."})
    assert "Snapshot verification" in html
    assert "Authority source" in html
    assert "Order lifecycle" in html
    assert "Ticket / Plan lineage" in html
    assert "Consistency" in html
