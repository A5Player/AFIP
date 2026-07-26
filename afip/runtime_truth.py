"""AFIP V1 authoritative read-only runtime truth model.

This module is the sole dashboard authority for process, broker-session,
financial-evidence, AFIP-runtime, and execution presentation state.  It never
initializes MT5 and never changes trading authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

SCHEMA_VERSION = "AFIP_V1_RUNTIME_TRUTH_V1"


def _upper(value: Any, default: str = "DATA_UNAVAILABLE") -> str:
    text = str(value or "").strip().upper()
    return text or default


def build_profile_truth(profile: Mapping[str, Any]) -> dict[str, Any]:
    process_alive = profile.get("process_alive") is True
    enabled = profile.get("enabled") is not False
    monitor_mode = _upper(profile.get("monitoring_mode"), "PASSIVE")
    raw_connection = _upper(profile.get("connection_status"))
    evidence_kind = _upper(profile.get("evidence_kind"))

    if not enabled:
        process_state = "DISABLED"
    elif process_alive:
        process_state = "RUNNING"
    else:
        process_state = "STOPPED"

    if monitor_mode == "ACTIVE" and raw_connection == "CONNECTED":
        session_state = "CONNECTED"
    elif process_alive:
        session_state = "NOT_VERIFIED_PASSIVE"
    else:
        session_state = "DISCONNECTED"

    # Backward-compatible broker-session contract.  New dashboards may use
    # the more descriptive ``session_state`` value, while established runtime
    # consumers require the stable values CONNECTED / NOT_VERIFIED /
    # DISCONNECTED.  Both fields are derived from the same authority and can
    # never disagree about whether a broker session is verified.
    if session_state == "CONNECTED":
        broker_session_state = "CONNECTED"
    elif session_state == "DISCONNECTED":
        broker_session_state = "DISCONNECTED"
    else:
        broker_session_state = "NOT_VERIFIED"

    has_financial = any(profile.get(k) is not None for k in ("balance", "equity", "free_margin", "bid", "ask"))
    snapshot_age = profile.get("snapshot_age_seconds")
    try:
        age = int(snapshot_age) if snapshot_age is not None else None
    except (TypeError, ValueError):
        age = None
    if monitor_mode == "ACTIVE" and raw_connection == "CONNECTED" and evidence_kind == "LIVE":
        financial_state = "LIVE"
    elif has_financial and age is not None and age <= 120:
        financial_state = "RECENT_SNAPSHOT"
    elif has_financial:
        financial_state = "STALE_SNAPSHOT"
    else:
        financial_state = "DATA_UNAVAILABLE"

    has_normalized_truth = isinstance(profile.get("runtime_truth"), Mapping)
    normalized = profile.get("runtime_truth") if has_normalized_truth else {}
    runtime_state = _upper(normalized.get("runtime_current") or profile.get("runtime_state") or profile.get("status"), "STOPPED")
    # Legacy direct callers do not carry source freshness metadata. Preserve
    # their established semantics; dashboard contracts always provide it.
    runtime_evidence_fresh = bool(normalized.get("runtime_evidence_fresh")) if has_normalized_truth else True
    execution_state = _upper(profile.get("execution") or profile.get("execution_authority"), "DATA_UNAVAILABLE")

    if not enabled:
        operational_state = "DISABLED"
        reason = "profile_disabled"
    elif runtime_state == "RUNNING" and runtime_evidence_fresh and process_alive:
        operational_state = "RUNNING"
        reason = "afip_runtime_and_mt5_process_running"
    elif runtime_state == "RUNNING" and runtime_evidence_fresh and not process_alive:
        if has_normalized_truth:
            operational_state = "WAITING_FOR_MT5"
            reason = "afip_runtime_running_waiting_for_user_started_mt5"
        else:
            operational_state = "DEGRADED"
            reason = "afip_runtime_running_but_mt5_process_stopped"
    elif runtime_state == "STALE":
        operational_state = "STALE"
        reason = "runtime_record_exists_but_heartbeat_is_stale"
    elif process_alive:
        operational_state = "IDLE"
        reason = "mt5_process_running_but_afip_runtime_not_running"
    else:
        operational_state = "STOPPED"
        reason = "no_active_afip_runtime"

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile_id": str(profile.get("profile_id", "UNKNOWN")).upper(),
        "process_state": process_state,
        "process_alive": process_alive,
        "session_state": session_state,
        "broker_session_state": broker_session_state,
        "financial_state": financial_state,
        "runtime_state": runtime_state,
        "runtime_evidence_fresh": runtime_evidence_fresh,
        "execution_state": execution_state,
        "operational_state": operational_state,
        "reason": reason,
        "monitoring_mode": monitor_mode,
        "connection_status": raw_connection,
        "evidence_kind": evidence_kind,
        "snapshot_age_seconds": age,
        "financial_live": financial_state == "LIVE",
        "financial_snapshot_available": financial_state in {"RECENT_SNAPSHOT", "STALE_SNAPSHOT"},
        "observation_current": True,
    }


def attach_runtime_truth_model(contract: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(contract)
    rows = []
    for value in payload.get("profiles", ()): 
        if not isinstance(value, Mapping):
            continue
        row = dict(value)
        truth = build_profile_truth(row)
        row["authoritative_runtime_truth"] = truth
        row["mt5_process_alive"] = truth["process_alive"]
        row["process_alive"] = truth["process_alive"]
        row["process_state"] = truth["process_state"]
        row["session_state"] = truth["session_state"]
        row["broker_session_state"] = truth["broker_session_state"]
        row["financial_state"] = truth["financial_state"]
        row["financial_live"] = truth["financial_live"]
        row["financial_snapshot_available"] = truth["financial_snapshot_available"]
        row["operational_state"] = truth["operational_state"]
        row["operational_reason"] = truth["reason"]
        row["connection_evidence_fresh"] = truth["observation_current"]
        rows.append(row)
    payload["profiles"] = rows
    payload["runtime_truth_model"] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy": "SINGLE_READ_ONLY_AUTHORITY",
        "mt5_initialization_allowed": False,
        "order_send_allowed": False,
    }
    return payload
