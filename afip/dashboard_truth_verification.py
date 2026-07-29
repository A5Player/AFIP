"""Read-only dashboard truth verification and lifecycle normalization.

This module only interprets existing AFIP evidence for presentation. It never
initializes MT5, changes execution permission, sizes positions, or sends orders.
"""
from __future__ import annotations

from typing import Any, Mapping

SCHEMA_VERSION = "AFIP_V1_DASHBOARD_TRUTH_VERIFICATION_V1"
_SUCCESS_RETCODES = {10008, 10009, 10010}


def _upper(value: Any, default: str = "DATA_UNAVAILABLE") -> str:
    text = str(value or "").strip().upper()
    return text or default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _tickets(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, (str, int, float)):
        return [str(value)]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item not in (None, "")]
    return []


def verify_snapshot(profile: Mapping[str, Any]) -> dict[str, Any]:
    metadata = profile.get("source_metadata") if isinstance(profile.get("source_metadata"), Mapping) else {}
    source = metadata.get("live_mt5_snapshot") if isinstance(metadata.get("live_mt5_snapshot"), Mapping) else {}
    required = ("balance", "equity", "free_margin", "bid", "ask", "connection_status")
    missing = [key for key in required if profile.get(key) in (None, "")]
    readable = bool(source.get("readable"))
    fresh = bool(source.get("fresh"))
    live = _upper(profile.get("evidence_kind"), "UNKNOWN") == "LIVE"
    connected = _upper(profile.get("connection_status"), "UNKNOWN") == "CONNECTED"
    verified = readable and fresh and live and connected and not missing
    if verified:
        reason = "live_snapshot_readable_fresh_connected_complete"
        status = "VERIFIED"
    elif not readable:
        reason = "live_snapshot_missing_or_unreadable"
        status = "NOT_VERIFIED"
    elif not fresh:
        reason = "live_snapshot_stale"
        status = "NOT_VERIFIED"
    elif not live:
        reason = "snapshot_not_labelled_live"
        status = "NOT_VERIFIED"
    elif not connected:
        reason = "snapshot_connection_not_connected"
        status = "NOT_VERIFIED"
    else:
        reason = "snapshot_missing_fields:" + ",".join(missing)
        status = "NOT_VERIFIED"
    return {
        "status": status,
        "verified": verified,
        "reason": reason,
        "source": str(source.get("path") or "runtime/profiles/<profile>/mt5_live_snapshot.json"),
        "age_seconds": source.get("age_seconds"),
        "required_fields": list(required),
        "missing_fields": missing,
    }


def execution_authority(profile: Mapping[str, Any]) -> dict[str, str]:
    metadata = profile.get("source_metadata") if isinstance(profile.get("source_metadata"), Mapping) else {}
    execution_meta = metadata.get("execution_state") if isinstance(metadata.get("execution_state"), Mapping) else {}
    execution_data = execution_meta.get("authority_data") if isinstance(execution_meta.get("authority_data"), Mapping) else {}
    raw = execution_data.get("execution") or execution_data.get("execution_mode")
    source = "EXECUTION_STATE"
    if raw in (None, ""):
        raw = profile.get("execution") or profile.get("execution_mode")
        source = "MERGED_PROFILE_EVIDENCE"
    authority = _upper(raw)
    aliases = {
        "DEMO": "DEMO_EXECUTION_ONLY",
        "DEMO_TRADING": "DEMO_EXECUTION_ONLY",
        "SIMULATION": "LOCKED_SIMULATION_ONLY",
        "PAPER": "LOCKED_SIMULATION_ONLY",
        "PAPER_TRADING": "LOCKED_SIMULATION_ONLY",
    }
    authority = aliases.get(authority, authority)
    return {"status": authority, "source": source}


def order_lifecycle(profile: Mapping[str, Any]) -> dict[str, Any]:
    sent_units = _int(profile.get("sent_units", profile.get("demo_sent_units", 0)))
    order_send_called = profile.get("order_send_called") is True
    order_check_called = profile.get("order_check_called") is True
    retcode = _int(profile.get("mt5_result_code"), default=-1)
    execution_tickets = _tickets(profile.get("tickets") or profile.get("last_ticket") or profile.get("last_order_ticket"))
    live_tickets = _tickets(profile.get("position_tickets") or profile.get("current_tickets"))
    raw = _upper(profile.get("order_status") or profile.get("demo_order_status"), "ORDER_NOT_SENT")
    accepted = retcode in _SUCCESS_RETCODES and order_send_called
    ticket_confirmed = bool(execution_tickets)
    live_match = bool(set(execution_tickets) & set(live_tickets))
    has_position = bool(live_tickets or profile.get("has_open_position") or _int(profile.get("positions_total")))

    if has_position and live_match:
        state = "POSITION_OPEN_MATCHED"
        current_order = "POSITION_OPEN"
        reason = "live_position_matches_execution_ticket"
    elif has_position:
        state = "POSITION_OPEN_UNMATCHED"
        current_order = "POSITION_OPEN_UNMATCHED"
        reason = "live_position_has_no_matching_execution_ticket"
    elif accepted and ticket_confirmed and sent_units > 0:
        state = "ORDER_ACCEPTED_POSITION_NOT_OPEN"
        current_order = "LAST_ORDER_ACCEPTED"
        reason = "mt5_accepted_ticket_recorded_no_current_position"
    elif order_send_called and accepted and not ticket_confirmed:
        state = "ORDER_ACCEPTED_TICKET_MISSING"
        current_order = "ORDER_SEND_NOT_CONFIRMED"
        reason = "mt5_acceptance_without_recorded_ticket"
    elif order_send_called and not accepted:
        state = "ORDER_SEND_FAILED_OR_REJECTED"
        current_order = "ORDER_NOT_SENT"
        reason = "order_send_called_without_success_retcode"
    elif sent_units > 0 or raw in {"ORDER_SENT", "DEMO_ORDER_SENT"}:
        state = "HISTORICAL_SENT_CLAIM_UNVERIFIED"
        current_order = "ORDER_SEND_NOT_CONFIRMED"
        reason = "sent_claim_without_complete_mt5_confirmation"
    elif order_check_called:
        state = "ORDER_CHECKED_NOT_SENT"
        current_order = "ORDER_NOT_SENT"
        reason = "order_check_completed_without_send"
    else:
        state = "NO_ORDER_SENT"
        current_order = "ORDER_NOT_SENT"
        reason = "no_current_order_send_evidence"

    return {
        "state": state,
        "current_order_status": current_order,
        "reason": reason,
        "raw_order_status": raw,
        "sent_units": sent_units,
        "order_check_called": order_check_called,
        "order_send_called": order_send_called,
        "mt5_result_code": None if retcode == -1 else retcode,
        "execution_tickets": execution_tickets,
        "live_tickets": live_tickets,
        "ticket_confirmed": ticket_confirmed,
        "live_match": live_match,
        "has_open_position": has_position,
    }


def lineage(profile: Mapping[str, Any], lifecycle: Mapping[str, Any]) -> dict[str, Any]:
    plan_id = profile.get("plan_id") or profile.get("trade_plan_id") or profile.get("active_trade_plan")
    trace_id = profile.get("execution_trace_id") or profile.get("decision_trace_id") or profile.get("trace_id")
    execution_tickets = list(lifecycle.get("execution_tickets") or [])
    live_tickets = list(lifecycle.get("live_tickets") or [])
    matched = list(sorted(set(execution_tickets) & set(live_tickets)))
    if matched and plan_id:
        status = "MATCHED"
        reason = "plan_and_execution_ticket_match_live_position"
    elif live_tickets and not matched:
        status = "UNMATCHED_LIVE_POSITION"
        reason = "live_ticket_not_found_in_current_execution_evidence"
    elif execution_tickets and not live_tickets:
        status = "HISTORICAL_ORDER_ONLY"
        reason = "execution_ticket_exists_without_current_position"
    elif plan_id or trace_id:
        status = "PLAN_OR_TRACE_ONLY"
        reason = "plan_or_trace_exists_without_ticket_lineage"
    else:
        status = "DATA_UNAVAILABLE"
        reason = "no_plan_trace_or_ticket_lineage_evidence"
    return {
        "status": status,
        "reason": reason,
        "plan_id": plan_id or "DATA_UNAVAILABLE",
        "trace_id": trace_id or "DATA_UNAVAILABLE",
        "execution_tickets": execution_tickets,
        "live_tickets": live_tickets,
        "matched_tickets": matched,
    }


def consistency(profile: Mapping[str, Any], snapshot: Mapping[str, Any], authority: Mapping[str, Any], lifecycle: Mapping[str, Any], lineage_record: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if profile.get("financial_live") and not snapshot.get("verified"):
        issues.append({"severity": "WARNING", "code": "LIVE_FINANCIAL_NOT_VERIFIED", "reason": str(snapshot.get("reason"))})
    if lifecycle.get("order_send_called") and authority.get("status") == "LOCKED_SIMULATION_ONLY":
        issues.append({"severity": "ERROR", "code": "ORDER_SEND_WITH_SIMULATION_AUTHORITY", "reason": "order_send_called_but_execution_authority_is_simulation"})
    if lifecycle.get("state") == "ORDER_ACCEPTED_TICKET_MISSING":
        issues.append({"severity": "ERROR", "code": "MT5_ACCEPTED_WITHOUT_TICKET", "reason": str(lifecycle.get("reason"))})
    if lifecycle.get("state") == "POSITION_OPEN_UNMATCHED":
        issues.append({"severity": "WARNING", "code": "POSITION_LINEAGE_UNMATCHED", "reason": str(lineage_record.get("reason"))})
    if lifecycle.get("current_order_status") == "POSITION_OPEN" and not lifecycle.get("has_open_position"):
        issues.append({"severity": "ERROR", "code": "POSITION_STATUS_WITHOUT_POSITION", "reason": "presentation_state_conflict"})
    status = "PASS" if not issues else "ERROR" if any(x["severity"] == "ERROR" for x in issues) else "WARNING"
    return {"status": status, "issue_count": len(issues), "issues": issues}


def attach_dashboard_truth_verification(contract: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(contract)
    profiles: list[dict[str, Any]] = []
    summary = {"VERIFIED": 0, "NOT_VERIFIED": 0, "PASS": 0, "WARNING": 0, "ERROR": 0}
    for item in payload.get("profiles", []):
        if not isinstance(item, Mapping):
            continue
        row = dict(item)
        snapshot = verify_snapshot(row)
        authority = execution_authority(row)
        metadata = row.get("source_metadata") if isinstance(row.get("source_metadata"), Mapping) else {}
        execution_meta = metadata.get("execution_state") if isinstance(metadata.get("execution_state"), Mapping) else {}
        execution_data = execution_meta.get("authority_data") if isinstance(execution_meta.get("authority_data"), Mapping) else {}
        lifecycle_input = dict(row)
        lifecycle_input.update(dict(execution_data))
        # Current live-position evidence remains authoritative for the present state.
        for key in ("position_tickets", "current_tickets", "positions_total", "has_open_position", "live_positions"):
            if key in row:
                lifecycle_input[key] = row.get(key)
        lifecycle_record = order_lifecycle(lifecycle_input)
        lineage_record = lineage(lifecycle_input, lifecycle_record)
        consistency_record = consistency(row, snapshot, authority, lifecycle_record, lineage_record)
        row["snapshot_verification"] = snapshot
        row["financial_snapshot_verified"] = bool(snapshot["verified"])
        row["execution_authority_truth"] = authority
        row["execution_authority_current"] = authority["status"]
        row["order_lifecycle"] = lifecycle_record
        row["normalized_order_status"] = lifecycle_record["current_order_status"]
        row["ticket_plan_lineage"] = lineage_record
        row["dashboard_consistency"] = consistency_record
        summary[snapshot["status"]] = summary.get(snapshot["status"], 0) + 1
        summary[consistency_record["status"]] = summary.get(consistency_record["status"], 0) + 1
        profiles.append(row)
    payload["profiles"] = profiles
    payload["dashboard_truth_verification"] = {
        "schema_version": SCHEMA_VERSION,
        "policy": "READ_ONLY_EVIDENCE_VERIFICATION_NO_EXECUTION_AUTHORITY",
        "summary": summary,
    }
    return payload
