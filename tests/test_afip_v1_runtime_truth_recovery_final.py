from __future__ import annotations

from afip.dashboard_operations_health import attach_operations_health
from afip.runtime_truth import attach_runtime_truth_model, build_profile_truth


def test_passive_terminal_process_never_claims_broker_connection() -> None:
    truth = build_profile_truth({
        "profile_id": "P1", "runtime_state": "RUNNING", "process_alive": True,
        "monitoring_mode": "PASSIVE", "connection_status": "CONNECTED_PASSIVE",
    })
    assert truth["process_state"] == "RUNNING"
    assert truth["broker_session_state"] == "NOT_VERIFIED"
    assert truth["financial_state"] == "DATA_UNAVAILABLE"


def test_closed_terminal_keeps_snapshot_but_is_degraded() -> None:
    truth = build_profile_truth({
        "profile_id": "P3", "runtime_state": "RUNNING", "process_alive": False,
        "monitoring_mode": "PASSIVE", "connection_status": "DISCONNECTED",
        "evidence_kind": "LAST_SNAPSHOT", "balance": 900.0,
        "snapshot_age_seconds": 30,
    })
    assert truth["process_state"] == "STOPPED"
    assert truth["broker_session_state"] == "DISCONNECTED"
    assert truth["financial_state"] == "RECENT_SNAPSHOT"
    assert truth["operational_state"] == "DEGRADED"


def test_operations_health_consumes_authoritative_runtime_truth() -> None:
    contract = attach_runtime_truth_model({"profiles": [{
        "profile_id": "P4", "runtime_state": "RUNNING", "process_alive": False,
        "monitoring_mode": "PASSIVE", "connection_status": "DISCONNECTED",
        "balance": 30.0, "snapshot_age_seconds": 20,
    }]})
    result = attach_operations_health(contract)
    row = result["profiles"][0]
    health = row["operations_health"]
    assert health["runtime_status"] == row["authoritative_runtime_truth"]["runtime_state"]
    assert health["mt5_process_status"] == row["authoritative_runtime_truth"]["process_state"]
    assert health["broker_session_status"] == row["authoritative_runtime_truth"]["broker_session_state"]
    assert health["financial_evidence_status"] == row["authoritative_runtime_truth"]["financial_state"]
