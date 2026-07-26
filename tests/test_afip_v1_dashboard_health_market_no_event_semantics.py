from afip.dashboard_state_machine import normalize_profile_state, attach_runtime_truth
from afip.dashboard_ui.split_runtime import _profile_rows


def _profile(**updates):
    row = {
        "profile_id": "P1",
        "runtime_state": "STOPPED",
        "connection_status": "CONNECTED",
        "execution": "LOCKED_SIMULATION_ONLY",
        "source_metadata": {
            "mt5_health": {"exists": True, "fresh": True},
            "profile_status": {"exists": True, "fresh": False},
            "execution_state": {"exists": False, "fresh": False},
        },
    }
    row.update(updates)
    return row


def test_stopped_runtime_with_fresh_mt5_is_idle_not_stale():
    truth = normalize_profile_state(_profile())
    assert truth["runtime_current"] == "STOPPED"
    assert truth["mt5_current"] == "CONNECTED"
    assert truth["gateway_current"] == "INACTIVE"
    assert truth["current_reason"] == "runtime_not_currently_running"
    assert truth["dashboard_health"] == "IDLE"


def test_no_execution_event_has_no_fake_timestamp_or_zero_age():
    truth = normalize_profile_state(_profile(order_status="ORDER_NOT_SENT", checked_at_utc="2099-01-01T00:00:00+00:00"))
    assert truth["last_gateway_event"] == "NONE_RECORDED"
    assert truth["last_gateway_event_at_utc"] is None
    assert truth["last_gateway_event_age_seconds"] is None


def test_runtime_truth_is_flattened_for_legacy_renderers():
    contract = attach_runtime_truth({"profiles": [_profile()]})
    row = contract["profiles"][0]
    assert row["current_runtime_status"] == "STOPPED"
    assert row["current_mt5_status"] == "CONNECTED"
    assert row["current_gateway_status"] == "INACTIVE"
    assert row["current_reason"] == "runtime_not_currently_running"


def test_operations_rows_use_truth_and_non_invented_inactive_semantics():
    contract = attach_runtime_truth({"profiles": [_profile()]})
    values = {label: value for _, label, value in _profile_rows(contract["profiles"][0])}
    assert values["Dashboard health"] == "IDLE"
    assert values["Runtime · current"] == "STOPPED"
    assert values["Gateway · current"] == "INACTIVE"
    assert values["Current reason"] == "runtime_not_currently_running"
    assert values["Last event time"] == "NOT_RECORDED"
    assert values["Last event age"] == "NOT_RECORDED"
    assert values["Decision"] == "NOT_EVALUATED"
    assert values["Regime"] == "NOT_EVALUATED"
    assert values["SL / TP"] == "NO_ACTIVE_POSITION"
