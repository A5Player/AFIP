from afip.dashboard_state_machine import normalize_profile_state, attach_runtime_truth


def test_stopped_runtime_separates_current_gateway_from_last_event():
    profile = {
        "runtime_state": "STOPPED",
        "connection_status": "CONNECTED",
        "gateway_status": "ORDER_SENT",
        "source_metadata": {
            "profile_status": {"exists": True, "fresh": True},
            "mt5_health": {"exists": True, "fresh": True},
            "execution_state": {"exists": True, "fresh": False, "modified_at_utc": "2026-07-25T00:00:00+00:00"},
        },
    }
    truth = normalize_profile_state(profile)
    assert truth["gateway_current"] == "INACTIVE"
    assert truth["last_gateway_event"] == "ORDER_SENT"
    assert truth["current_reason"] == "runtime_not_currently_running"


def test_stale_execution_is_not_reported_as_current_block():
    profile = {
        "runtime_state": "RUNNING",
        "connection_status": "CONNECTED",
        "gateway_status": "BLOCKED",
        "source_metadata": {
            "profile_status": {"exists": True, "fresh": True},
            "mt5_health": {"exists": True, "fresh": True},
            "execution_state": {"exists": True, "fresh": False},
        },
    }
    truth = normalize_profile_state(profile)
    assert truth["gateway_current"] == "STALE"
    assert truth["current_reason"] == "execution_state_stale"


def test_attach_runtime_truth_keeps_contract_read_only_semantics():
    original = {"profiles": [{"profile_id": "P1", "runtime_state": "STOPPED"}]}
    result = attach_runtime_truth(original)
    assert "runtime_truth" not in original["profiles"][0]
    assert result["profiles"][0]["runtime_truth"]["gateway_current"] == "INACTIVE"
