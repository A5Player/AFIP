from afip.runtime_truth import build_profile_truth, attach_runtime_truth_model


def test_stopped_terminal_cannot_be_presented_as_running_operation():
    truth = build_profile_truth({
        "profile_id": "P3", "enabled": True, "runtime_state": "RUNNING",
        "process_alive": False, "monitoring_mode": "PASSIVE",
        "connection_status": "DISCONNECTED", "evidence_kind": "LAST_VERIFIED_SNAPSHOT",
        "balance": 900.0, "snapshot_age_seconds": 30,
    })
    assert truth["process_state"] == "STOPPED"
    assert truth["session_state"] == "DISCONNECTED"
    assert truth["operational_state"] == "DEGRADED"
    assert truth["financial_state"] == "RECENT_SNAPSHOT"


def test_passive_process_is_not_claimed_as_verified_broker_session():
    truth = build_profile_truth({
        "profile_id": "P1", "enabled": True, "runtime_state": "RUNNING",
        "process_alive": True, "monitoring_mode": "PASSIVE",
        "connection_status": "CONNECTED_PASSIVE", "evidence_kind": "LAST_VERIFIED_SNAPSHOT",
    })
    assert truth["process_state"] == "RUNNING"
    assert truth["session_state"] == "NOT_VERIFIED_PASSIVE"
    assert truth["operational_state"] == "RUNNING"
    assert truth["financial_live"] is False


def test_active_live_requires_all_live_evidence():
    truth = build_profile_truth({
        "profile_id": "P2", "enabled": True, "runtime_state": "RUNNING",
        "process_alive": True, "monitoring_mode": "ACTIVE",
        "connection_status": "CONNECTED", "evidence_kind": "LIVE", "balance": 300.0,
    })
    assert truth["session_state"] == "CONNECTED"
    assert truth["financial_state"] == "LIVE"


def test_contract_attachment_overwrites_derived_dashboard_fields():
    payload = attach_runtime_truth_model({"profiles": [{
        "profile_id": "P4", "enabled": True, "runtime_state": "RUNNING",
        "process_alive": False, "connection_status": "DISCONNECTED",
        "monitoring_mode": "PASSIVE", "financial_live": True,
    }]})
    row = payload["profiles"][0]
    assert row["financial_live"] is False
    assert row["operational_state"] == "DEGRADED"
    assert row["process_state"] == "STOPPED"
