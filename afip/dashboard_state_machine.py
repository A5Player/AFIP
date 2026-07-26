"""Read-only AFIP dashboard runtime state normalization.

Separates current state from historical events. This module has no execution,
position-sizing, MT5 initialization, or order authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


def _upper(value: Any, default: str) -> str:
    text = str(value if value not in (None, "") else default).strip().upper()
    return text or default


def _timestamp(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        text = str(value).strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _age_seconds(value: Any) -> int | None:
    parsed = _timestamp(value)
    if parsed is None:
        return None
    return max(0, int((datetime.now(timezone.utc) - parsed).total_seconds()))


def _market_state(profile: Mapping[str, Any]) -> tuple[str, str]:
    explicit = profile.get("market_status", profile.get("market_session_status"))
    if explicit not in (None, "", "UNKNOWN"):
        return _upper(explicit, "UNKNOWN"), "RUNTIME_EVIDENCE"
    # Gold/FX trading is closed over the ordinary UTC weekend. This is a
    # presentation-only calendar inference and never grants execution authority.
    if datetime.now(timezone.utc).weekday() >= 5:
        return "CLOSED_WEEKEND", "UTC_WEEKEND_CALENDAR"
    return "UNKNOWN", "NO_MARKET_SESSION_EVIDENCE"


def normalize_profile_state(profile: Mapping[str, Any]) -> dict[str, Any]:
    metadata = profile.get("source_metadata") if isinstance(profile.get("source_metadata"), Mapping) else {}
    mt5_meta = metadata.get("mt5_health") if isinstance(metadata.get("mt5_health"), Mapping) else {}
    status_meta = metadata.get("profile_status") if isinstance(metadata.get("profile_status"), Mapping) else {}
    execution_meta = metadata.get("execution_state") if isinstance(metadata.get("execution_state"), Mapping) else {}

    runtime_raw = _upper(profile.get("runtime_state", profile.get("status")), "STOPPED")
    runtime_fresh = bool(status_meta.get("fresh"))
    # A stale RUNNING record is unsafe to present as current. A stale STOPPED
    # record remains STOPPED because no live evidence claims the process runs.
    if runtime_fresh:
        runtime_current = runtime_raw
    elif runtime_raw in {"STOPPED", "INACTIVE", "NOT_STARTED", "DISABLED"}:
        runtime_current = runtime_raw
    elif status_meta.get("exists"):
        runtime_current = "STALE"
    else:
        runtime_current = runtime_raw

    mt5_raw = _upper(profile.get("mt5_connection", profile.get("connection_status")), "NOT_CHECKED")
    mt5_current = mt5_raw if bool(mt5_meta.get("fresh")) else "STALE" if mt5_meta.get("exists") else "DATA_UNAVAILABLE"

    event = _upper(
        profile.get("demo_gateway_status", profile.get("gateway_status", profile.get("demo_order_status", profile.get("order_status")))),
        "NONE_RECORDED",
    )
    event_recorded = bool(execution_meta.get("exists")) and event not in {
        "", "NONE", "NONE_RECORDED", "NOT_RECORDED", "DATA_UNAVAILABLE", "ORDER_NOT_SENT"
    }
    if event_recorded:
        event_time = (
            profile.get("execution_checked_at_utc")
            or profile.get("last_execution_at_utc")
            or execution_meta.get("modified_at_utc")
        )
    else:
        event = "NONE_RECORDED"
        event_time = None
    event_age = _age_seconds(event_time)
    event_fresh = bool(execution_meta.get("fresh")) and event_recorded

    running = runtime_current == "RUNNING"
    if not running:
        gateway_current = "INACTIVE"
        reason = "runtime_not_currently_running"
    elif not event_fresh:
        gateway_current = "STALE" if execution_meta.get("exists") else "DATA_UNAVAILABLE"
        reason = "execution_state_stale" if execution_meta.get("exists") else "execution_state_unavailable"
    elif event in {"BLOCKED", "REJECTED", "FAILED"}:
        gateway_current = "BLOCKED"
        reason = str(profile.get("demo_gateway_reason") or profile.get("waiting_reason") or "gateway_blocked")
    elif event in {"ORDER_SENT", "SENDING", "EXECUTING"}:
        gateway_current = "ACTIVE"
        reason = str(profile.get("demo_gateway_reason") or "execution_event_active")
    elif event in {"READY", "WAITING", "INACTIVE", "NOT_STARTED"}:
        gateway_current = event
        reason = str(profile.get("demo_gateway_reason") or profile.get("waiting_reason") or "waiting_for_runtime_evidence")
    else:
        gateway_current = "DATA_UNAVAILABLE"
        reason = "execution_state_unavailable"

    market_current, market_source = _market_state(profile)
    if mt5_current == "STALE":
        health = "STALE"
    elif mt5_current == "DATA_UNAVAILABLE":
        health = "REVIEW"
    elif mt5_current == "CONNECTED" and runtime_current == "RUNNING" and gateway_current != "BLOCKED":
        health = "READY"
    elif mt5_current == "CONNECTED" and runtime_current in {"STOPPED", "INACTIVE", "NOT_STARTED", "DISABLED"}:
        health = "IDLE"
    elif runtime_current == "STALE":
        health = "STALE"
    else:
        health = "REVIEW"

    return {
        "market_current": market_current,
        "market_current_source": market_source,
        "runtime_current": runtime_current,
        "runtime_evidence_fresh": runtime_fresh,
        "mt5_current": mt5_current,
        "mt5_evidence_fresh": bool(mt5_meta.get("fresh")),
        "execution_authority_current": _upper(profile.get("execution", profile.get("execution_mode")), "DATA_UNAVAILABLE"),
        "gateway_current": gateway_current,
        "gateway_evidence_fresh": event_fresh,
        "current_reason": reason,
        "last_gateway_event": event,
        "last_gateway_event_at_utc": str(event_time) if event_time not in (None, "") else None,
        "last_gateway_event_age_seconds": event_age,
        "last_gateway_event_fresh": event_fresh,
        "dashboard_health": health,
    }


def attach_runtime_truth(contract: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(contract)
    profiles = []
    for row in payload.get("profiles", []):
        if not isinstance(row, Mapping):
            continue
        normalized = dict(row)
        truth = normalize_profile_state(normalized)
        normalized["runtime_truth"] = truth
        # Compatibility aliases keep all dashboard renderers on the same truth.
        normalized.update({
            "current_runtime_status": truth["runtime_current"],
            "current_mt5_status": truth["mt5_current"],
            "current_gateway_status": truth["gateway_current"],
            "current_reason": truth["current_reason"],
            "last_gateway_event": truth["last_gateway_event"],
            "last_gateway_event_at_utc": truth["last_gateway_event_at_utc"],
        })
        profiles.append(normalized)
    payload["profiles"] = profiles
    counts: dict[str, int] = {}
    for row in profiles:
        state = row.get("runtime_truth", {}).get("dashboard_health", "REVIEW")
        counts[state] = counts.get(state, 0) + 1
    payload["runtime_truth_summary"] = {
        "profiles": len(profiles),
        "health_counts": counts,
        "policy": "CURRENT_STATE_SEPARATE_FROM_LAST_EVENT",
    }
    return payload
