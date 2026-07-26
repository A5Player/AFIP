"""Read-only AFIP operations-health and evidence-semantics adapter.

This module explains what the dashboard knows, does not know, and has not yet
collected. It never starts runtimes, initializes MT5, calculates lot authority,
or sends orders.
"""
from __future__ import annotations

from typing import Any, Mapping


_STOPPED = {"STOPPED", "INACTIVE", "NOT_STARTED", "DISABLED"}


def _text(value: Any, default: str) -> str:
    text = str(value if value not in (None, "") else default).strip().upper()
    return text or default


def _has(profile: Mapping[str, Any], *keys: str) -> bool:
    return any(profile.get(key) not in (None, "", [], {}) for key in keys)


def assess_profile_operations(profile: Mapping[str, Any]) -> dict[str, Any]:
    authoritative = profile.get("authoritative_runtime_truth") if isinstance(profile.get("authoritative_runtime_truth"), Mapping) else {}
    legacy_truth = profile.get("runtime_truth") if isinstance(profile.get("runtime_truth"), Mapping) else {}
    runtime = _text(authoritative.get("runtime_state", legacy_truth.get("runtime_current")), "DATA_UNAVAILABLE")
    process_state = _text(authoritative.get("process_state"), "DATA_UNAVAILABLE")
    session_state = _text(authoritative.get("broker_session_state", authoritative.get("session_state", legacy_truth.get("mt5_current"))), "DATA_UNAVAILABLE")
    market = _text(legacy_truth.get("market_current"), "UNKNOWN")
    gateway = _text(legacy_truth.get("gateway_current"), "DATA_UNAVAILABLE")
    authority = _text(authoritative.get("execution_state", legacy_truth.get("execution_authority_current")), "DATA_UNAVAILABLE")
    financial_state = _text(authoritative.get("financial_state", profile.get("financial_state")), "DATA_UNAVAILABLE")
    if not authoritative and financial_state == "DATA_UNAVAILABLE":
        legacy_financial_live = all(_has(profile, key) for key in ("balance", "equity", "free_margin", "bid", "ask"))
        if session_state == "CONNECTED" and legacy_financial_live:
            financial_state = "LIVE"

    if financial_state == "LIVE":
        financial_status = "READY"
    elif financial_state in {"RECENT_SNAPSHOT", "STALE_SNAPSHOT", "DATA_UNAVAILABLE"}:
        financial_status = financial_state
    else:
        financial_status = "REVIEW"
    mt5 = "CONNECTED" if session_state == "CONNECTED" else process_state

    if runtime in _STOPPED and mt5 == "CONNECTED":
        operating_mode = "MONITORING_ONLY"
        overall = "IDLE_READY"
        reason = "mt5_connected_runtime_stopped"
    elif runtime == "RUNNING" and mt5 == "CONNECTED" and gateway not in {"BLOCKED", "FAILED"}:
        operating_mode = "ACTIVE_RUNTIME"
        overall = "READY"
        reason = "runtime_and_mt5_current"
    elif runtime == "STALE" or mt5 == "STALE":
        operating_mode = "EVIDENCE_STALE"
        overall = "STALE"
        reason = "current_evidence_stale"
    elif mt5 == "DATA_UNAVAILABLE":
        operating_mode = "MT5_NOT_OBSERVED"
        overall = "REVIEW"
        reason = "mt5_evidence_unavailable"
    else:
        operating_mode = "REVIEW_REQUIRED"
        overall = "REVIEW"
        reason = "operational_state_requires_review"

    # Evidence semantics: these labels explicitly avoid presenting an absent
    # collector as a financial zero.
    today_pl = "AVAILABLE" if _has(profile, "daily_profit", "today_profit", "realized_profit_today") else "NOT_COLLECTED"
    cash_flow = "AVAILABLE" if _has(profile, "deposits", "total_deposits", "withdrawals", "total_withdrawals") else "NOT_TRACKED"
    reserve = "AVAILABLE" if _has(profile, "reserve", "configured_reserve") else "NOT_CONFIGURED"
    if _has(profile, "available_allocation", "allocation"):
        allocation = "AVAILABLE"
    elif runtime in _STOPPED:
        allocation = "NOT_EVALUATED_RUNTIME_STOPPED"
    else:
        allocation = "NOT_EVALUATED"

    if market.startswith("CLOSED"):
        decision_semantic = "NOT_EVALUATED_MARKET_CLOSED"
    elif runtime in _STOPPED:
        decision_semantic = "NOT_EVALUATED_RUNTIME_STOPPED"
    elif _has(profile, "decision_action", "action"):
        decision_semantic = "AVAILABLE"
    else:
        decision_semantic = "NOT_RECORDED"

    return {
        "overall_status": overall,
        "operating_mode": operating_mode,
        "reason": reason,
        "financial_status": financial_status,
        "runtime_status": runtime,
        "mt5_status": mt5,
        "mt5_process_status": process_state,
        "broker_session_status": session_state,
        "financial_evidence_status": financial_state,
        "market_status": market,
        "gateway_status": gateway,
        "execution_authority": authority,
        "today_realized_pl_status": today_pl,
        "cash_flow_status": cash_flow,
        "reserve_status": reserve,
        "available_allocation_status": allocation,
        "decision_evidence_status": decision_semantic,
        "policy": "ABSENT_EVIDENCE_IS_NEVER_RENDERED_AS_ZERO",
    }


def attach_operations_health(contract: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(contract)
    profiles: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for row in payload.get("profiles", []):
        if not isinstance(row, Mapping):
            continue
        normalized = dict(row)
        health = assess_profile_operations(normalized)
        normalized["operations_health"] = health
        counts[health["overall_status"]] = counts.get(health["overall_status"], 0) + 1
        profiles.append(normalized)
    payload["profiles"] = profiles

    total = len(profiles)
    connected = sum(1 for p in profiles if p.get("operations_health", {}).get("mt5_status") == "CONNECTED")
    running = sum(1 for p in profiles if p.get("operations_health", {}).get("runtime_status") == "RUNNING")
    monitoring = sum(1 for p in profiles if p.get("operations_health", {}).get("operating_mode") == "MONITORING_ONLY")
    if total and connected == total and running == total:
        overall = "READY"
    elif total and connected == total and monitoring == total:
        overall = "MONITORING_ONLY"
    elif counts.get("STALE"):
        overall = "STALE"
    else:
        overall = "REVIEW"
    payload["operations_health_summary"] = {
        "status": overall,
        "profiles": total,
        "mt5_connected_profiles": connected,
        "runtime_running_profiles": running,
        "monitoring_only_profiles": monitoring,
        "status_counts": counts,
        "read_only": True,
    }
    return payload
