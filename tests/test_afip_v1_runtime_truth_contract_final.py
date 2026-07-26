from afip.runtime_truth import attach_runtime_truth_model, build_profile_truth


def test_passive_running_terminal_preserves_legacy_broker_session_contract() -> None:
    truth = build_profile_truth({
        "profile_id": "P1",
        "runtime_state": "RUNNING",
        "process_alive": True,
        "monitoring_mode": "PASSIVE",
        "connection_status": "CONNECTED_PASSIVE",
    })
    assert truth["process_state"] == "RUNNING"
    assert truth["session_state"] == "NOT_VERIFIED_PASSIVE"
    assert truth["broker_session_state"] == "NOT_VERIFIED"


def test_stopped_terminal_reports_disconnected_broker_session() -> None:
    truth = build_profile_truth({
        "profile_id": "P3",
        "runtime_state": "RUNNING",
        "process_alive": False,
        "monitoring_mode": "PASSIVE",
        "connection_status": "DISCONNECTED",
        "evidence_kind": "LAST_SNAPSHOT",
        "balance": 900.0,
        "snapshot_age_seconds": 30,
    })
    assert truth["process_state"] == "STOPPED"
    assert truth["broker_session_state"] == "DISCONNECTED"


def test_contract_row_exposes_broker_session_compatibility_field() -> None:
    contract = attach_runtime_truth_model({"profiles": [{
        "profile_id": "P4",
        "runtime_state": "RUNNING",
        "process_alive": False,
        "monitoring_mode": "PASSIVE",
        "connection_status": "DISCONNECTED",
    }]})
    row = contract["profiles"][0]
    assert row["broker_session_state"] == row["authoritative_runtime_truth"]["broker_session_state"]
