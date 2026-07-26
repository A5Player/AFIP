"""Read-only AFIP V1 order evidence dashboard.

Current runtime truth and historical execution evidence are intentionally kept
separate. This module never initializes MT5, calculates authority, modifies
runtime state, or sends orders.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Mapping

ORDER_EVIDENCE_SCHEMA_VERSION = "AFIP_V1_ORDER_EVIDENCE_DASHBOARD_V2"
ORDER_EVIDENCE_FILENAME = "afip_order_evidence_dashboard.html"


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def _text(value: Any, default: str = "DATA_UNAVAILABLE") -> str:
    if value is None or value == "":
        return default
    return str(value)


def _bool_text(value: Any) -> str:
    if value is True:
        return "YES"
    if value is False:
        return "NO"
    return "DATA_UNAVAILABLE"


def _market_state(profile: Mapping[str, Any]) -> str:
    truth = _mapping(profile.get("runtime_truth"))
    direct = _first(truth, "market_current") or _first(profile, "market_state", "market_status", "session_status")
    if direct is not None:
        text = str(direct).upper()
        if "CLOSED" in text:
            return text
        if "OPEN" in text:
            return text
    market_open = _first(profile, "market_open", "is_market_open")
    if market_open is False:
        return "MARKET_CLOSED"
    if market_open is True:
        return "MARKET_OPEN"
    return "DATA_UNAVAILABLE"


def _historical_status(record: Mapping[str, Any], market_state: str) -> str:
    raw = str(_first(record, "order_status", "gateway_status", "status", "runtime_state") or "").upper()
    reason = str(_first(record, "gateway_reason", "waiting_reason", "reason", "trading_block_reason") or "").upper()
    if "SENT" in raw and "NOT" not in raw:
        return "ORDER_SENT"
    if any(token in raw for token in ("FAIL", "ERROR", "REJECT")):
        return "FAILED"
    if any(token in reason for token in ("BLOCK", "INSUFFICIENT", "TOO_HIGH", "NOT_APPROVED", "MISMATCH", "OUT_OF_RANGE")):
        return "BLOCKED"
    if market_state.startswith("CLOSED") or market_state == "MARKET_CLOSED":
        if raw in {"", "WAITING", "ORDER_NOT_SENT", "STOPPED"}:
            return "MARKET_CLOSED"
    if raw in {"WAITING", "ORDER_NOT_SENT", "STOPPED", "PENDING"}:
        return "WAITING"
    return raw or "NONE_RECORDED"


def _ticket_values(record: Mapping[str, Any]) -> list[str]:
    value = _first(record, "tickets", "order_tickets", "position_tickets", "ticket")
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if item is not None]
    if value is not None:
        return [str(value)]
    result = _mapping(record.get("mt5_result"))
    ticket = _first(result, "order", "deal", "ticket")
    return [str(ticket)] if ticket is not None else []


def build_order_evidence(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one profile without promoting historical events to current."""
    decision = _mapping(profile.get("decision_pipeline"))
    intelligence = _mapping(profile.get("intelligence_snapshot"))
    authority = _mapping(profile.get("authority_snapshot"))
    trace = _mapping(profile.get("execution_trace"))
    truth = _mapping(profile.get("runtime_truth"))
    market_state = _market_state(profile)

    historical_status = _historical_status(profile, market_state)
    historical_reason = _first(profile, "gateway_reason", "waiting_reason", "reason", "trading_block_reason")
    if historical_reason is None and historical_status == "MARKET_CLOSED":
        historical_reason = "market_closed_no_new_execution_expected"

    runtime_current = _text(
        _first(truth, "runtime_current") or _first(profile, "current_runtime_status", "runtime_state", "status"),
        "STOPPED",
    ).upper()
    gateway_current = _text(
        _first(truth, "gateway_current") or _first(profile, "current_gateway_status"),
        "DATA_UNAVAILABLE",
    ).upper()
    current_reason = _text(
        _first(truth, "current_reason") or _first(profile, "current_reason"),
        "execution_state_unavailable",
    )
    execution_authority = _text(
        _first(truth, "execution_authority_current") or _first(profile, "execution", "execution_mode")
    )

    market_closed = "CLOSED" in market_state
    if market_closed:
        current_order_status = "NO_CURRENT_ORDER"
        current_permission = "MARKET_CLOSED"
        if current_reason in {"DATA_UNAVAILABLE", "execution_state_unavailable"}:
            current_reason = "market_closed_no_new_execution_expected"
    elif runtime_current not in {"RUNNING", "READY", "ACTIVE"}:
        current_order_status = "NO_CURRENT_ORDER"
        current_permission = "NOT_EVALUATED_RUNTIME_STOPPED"
        if current_reason == "DATA_UNAVAILABLE":
            current_reason = "runtime_not_currently_running"
    elif gateway_current in {"BLOCKED", "REJECTED", "FAILED"}:
        current_order_status = "BLOCKED"
        current_permission = "BLOCKED"
    elif gateway_current in {"ACTIVE", "SENDING", "EXECUTING"}:
        current_order_status = "EXECUTION_ACTIVE"
        current_permission = "PASS"
    else:
        current_order_status = "NO_CURRENT_ORDER"
        current_permission = "NOT_EVALUATED"

    direction = _first(profile, "decision", "direction", "side", "entry_direction")
    confidence = _first(profile, "confidence", "decision_confidence", "confidence_score")
    if confidence is None:
        confidence = _first(intelligence, "confidence", "decision_confidence", "score")

    historical_timestamp = (
        _first(truth, "last_gateway_event_at_utc")
        or _first(profile, "execution_checked_at_utc", "last_execution_at_utc", "timestamp_utc", "updated_at_utc", "last_update_utc", "generated_at_utc")
    )

    return {
        "profile_id": _text(profile.get("profile_id"), "UNKNOWN"),
        "profile_name": _text(_first(profile, "profile_name", "name"), ""),
        "market_state": market_state,
        "current_runtime_status": runtime_current,
        "current_gateway_status": gateway_current,
        "current_order_status": current_order_status,
        "current_permission": current_permission,
        "current_reason": current_reason,
        "execution_authority_current": execution_authority,
        "historical_status": historical_status,
        "historical_reason": _text(historical_reason, "NONE_RECORDED"),
        "historical_timestamp_utc": _text(historical_timestamp, "NOT_RECORDED"),
        "historical_age_seconds": _first(truth, "last_gateway_event_age_seconds") if _first(truth, "last_gateway_event_age_seconds") is not None else profile.get("data_age_seconds"),
        # Compatibility aliases retained for existing consumers/tests.
        "evidence_status": historical_status,
        "reason": _text(historical_reason, "NONE_RECORDED"),
        "trace_id": _text(_first(profile, "execution_trace_id", "trace_id", "decision_trace_id")),
        "timestamp_utc": _text(historical_timestamp, "NOT_RECORDED"),
        "data_status": _text(profile.get("data_status")),
        "data_age_seconds": profile.get("data_age_seconds"),
        "decision": _text(direction),
        "confidence": confidence if confidence is not None else "DATA_UNAVAILABLE",
        "pattern": _text(_first(profile, "pattern", "pattern_name", "pattern_family", "graph_pattern")),
        "market_regime": _text(_first(profile, "market_regime", "regime", "market_regime_name")),
        "multi_timeframe": _text(_first(profile, "multi_timeframe", "multi_timeframe_status", "mtf_status")),
        "capital_authority": _text(_first(authority, "capital_authority", "capital_status") or _first(decision, "capital_authority", "capital_status") or _first(profile, "capital_authority", "capital_status")),
        "lot_authority": _text(_first(authority, "lot_authority", "lot_status") or _first(decision, "lot_authority", "lot_status") or _first(profile, "lot_authority", "lot_status")),
        "risk_authority": _text(_first(authority, "risk_authority", "risk_status") or _first(decision, "risk_authority", "risk_status") or _first(profile, "risk_authority", "risk_status")),
        "trading_cost": _text(_first(profile, "trading_cost_status", "spread_status", "trading_cost_allowed")),
        "approved_units": _first(profile, "approved_units", "allocated_units", "units"),
        "sent_units": _first(profile, "sent_units", "orders_sent"),
        "lot_per_unit": _first(profile, "lot_per_unit", "base_lot"),
        "approved_lot": _first(profile, "approved_lot", "lot_size", "volume"),
        "entry_price": _first(profile, "entry_price", "price", "request_price"),
        "stop_loss": _first(profile, "stop_loss", "sl", "approved_sl"),
        "take_profit": _first(profile, "take_profit", "tp", "approved_tp"),
        "spread_points": _first(profile, "spread_points", "current_spread_points"),
        "order_check_called": _bool_text(_first(profile, "order_check_called")),
        "order_send_called": _bool_text(_first(profile, "order_send_called")),
        "mt5_result_code": _text(_first(profile, "mt5_result_code", "retcode")),
        "mt5_result_comment": _text(_first(profile, "mt5_result_comment", "comment")),
        "tickets": _ticket_values(profile),
        "source_metadata": dict(_mapping(profile.get("source_metadata"))),
        "raw_evidence_available": any(bool(x) for x in (decision, intelligence, authority, trace)),
    }


def attach_order_evidence(contract: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(contract)
    profiles: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for item in contract.get("profiles", []):
        if not isinstance(item, Mapping):
            continue
        row = dict(item)
        evidence = build_order_evidence(row)
        row["order_evidence"] = evidence
        profiles.append(row)
        records.append(evidence)
    result["profiles"] = profiles
    result["order_evidence"] = records
    result["order_evidence_schema_version"] = ORDER_EVIDENCE_SCHEMA_VERSION
    return result


def _value(value: Any) -> str:
    if value is None or value == "":
        return "DATA_UNAVAILABLE"
    if isinstance(value, float):
        return f"{value:.5f}".rstrip("0").rstrip(".")
    return str(value)


def _field(label: str, value: Any) -> str:
    return f'<div class="field"><span>{escape(label)}</span><b>{escape(_value(value))}</b></div>'


def render_order_evidence_dashboard(contract: Mapping[str, Any]) -> str:
    generated = escape(_text(contract.get("generated_at_utc"), datetime.now(timezone.utc).isoformat()))
    cards: list[str] = []
    for record in contract.get("order_evidence", []):
        if not isinstance(record, Mapping):
            continue
        tickets = ", ".join(record.get("tickets", [])) if isinstance(record.get("tickets"), list) else "DATA_UNAVAILABLE"
        tickets = tickets or "DATA_UNAVAILABLE"
        source_paths = [
            str(source["path"])
            for source in _mapping(record.get("source_metadata")).values()
            if isinstance(source, Mapping) and source.get("path")
        ]
        source_text = " · ".join(source_paths) or "DATA_UNAVAILABLE"
        current_status = _text(record.get("current_order_status"), "NO_CURRENT_ORDER")
        historical_status = _text(record.get("historical_status"), "NONE_RECORDED")
        cards.append(
            f'''<section class="card current-{escape(current_status.lower())}">
<header><div><h2>{escape(_text(record.get("profile_id")))} · {escape(_text(record.get("profile_name"), ""))}</h2><p>Current truth and last evidence</p></div><div class="badges"><span>{escape(_text(record.get("market_state")))}</span><strong>{escape(current_status)}</strong></div></header>
<div class="current"><h3>Current Runtime Truth</h3>{_field("Runtime", record.get("current_runtime_status"))}{_field("Gateway", record.get("current_gateway_status"))}{_field("Order status", record.get("current_order_status"))}{_field("Permission", record.get("current_permission"))}{_field("Execution authority", record.get("execution_authority_current"))}<div class="reason current-reason">Current reason: <b>{escape(_text(record.get("current_reason")))}</b></div></div>
<div class="history-head"><div><h3>Last Historical Evidence</h3><p>{escape(_text(record.get("historical_timestamp_utc"), "NOT_RECORDED"))}</p></div><span>{escape(historical_status)}</span></div>
<div class="reason">Historical reason: <b>{escape(_text(record.get("historical_reason")))}</b></div>
<div class="groups">
<div><h3>Decision Evidence</h3>{_field("Trace ID", record.get("trace_id"))}{_field("Decision", record.get("decision"))}{_field("Confidence", record.get("confidence"))}{_field("Pattern", record.get("pattern"))}{_field("Market regime", record.get("market_regime"))}{_field("Multi-timeframe", record.get("multi_timeframe"))}</div>
<div><h3>Authority Evidence</h3>{_field("Capital", record.get("capital_authority"))}{_field("Lot", record.get("lot_authority"))}{_field("Risk", record.get("risk_authority"))}{_field("Trading cost", record.get("trading_cost"))}{_field("Spread points", record.get("spread_points"))}</div>
<div><h3>Order Parameters</h3>{_field("Approved units", record.get("approved_units"))}{_field("Sent units", record.get("sent_units"))}{_field("Lot per unit", record.get("lot_per_unit"))}{_field("Approved lot", record.get("approved_lot"))}{_field("Entry", record.get("entry_price"))}{_field("SL", record.get("stop_loss"))}{_field("TP", record.get("take_profit"))}</div>
<div><h3>MT5 Evidence</h3>{_field("order_check called", record.get("order_check_called"))}{_field("order_send called", record.get("order_send_called"))}{_field("Result code", record.get("mt5_result_code"))}{_field("Result comment", record.get("mt5_result_comment"))}{_field("Tickets", tickets)}</div>
</div><footer>Historical data: {escape(_text(record.get("data_status")))} · Age: {escape(_value(record.get("historical_age_seconds")))} sec · Sources: {escape(source_text)}</footer></section>'''
        )
    empty = '<section class="empty">No order or execution-attempt evidence is available.</section>' if not cards else ""
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="5">
<title>AFIP Order Evidence</title><style>
:root{{font-family:Arial,"Noto Sans Thai",sans-serif;color:#172033;background:#eef2f7}}*{{box-sizing:border-box}}html,body{{min-height:100%;overflow:auto}}body{{margin:0;padding:16px 16px 140px}}.top{{display:flex;justify-content:space-between;gap:15px;align-items:end;margin-bottom:16px}}h1{{margin:0;font-size:24px}}.top p{{margin:5px 0 0;color:#64748b}}.policy{{font-size:11px;background:#e8fff3;border:1px solid #9be0bc;padding:9px 12px;border-radius:10px}}.notice{{margin-bottom:15px;padding:12px 14px;background:#fff8dc;border:1px solid #efd276;border-radius:10px;font-size:12px}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:start}}.card{{background:#fff;border:1px solid #dce4ef;border-radius:14px;overflow:hidden;box-shadow:0 5px 16px #1720330c}}header{{display:flex;justify-content:space-between;gap:10px;padding:11px 12px;border-bottom:1px solid #e8edf4}}h2{{font-size:17px;margin:0}}header p,.history-head p{{font-size:10px;color:#64748b;margin:5px 0 0}}.badges{{display:flex;gap:6px;align-items:start;flex-wrap:wrap;justify-content:end}}.badges span,.badges strong,.history-head span{{font-size:9px;padding:6px 8px;border-radius:999px;background:#eef2f7}}.badges strong{{background:#dbeafe;color:#1d4ed8}}.current-no_current_order .badges strong{{background:#f1f5f9;color:#475569}}.current-blocked .badges strong{{background:#fee2e2;color:#b91c1c}}.current-execution_active .badges strong{{background:#dcfce7;color:#15803d}}.current{{padding:10px 12px;background:#f8fbff;border-bottom:1px solid #dbe7f3}}.current h3{{color:#1d4ed8}}.current-reason{{margin:8px -12px -10px}}.history-head{{display:flex;justify-content:space-between;gap:8px;align-items:start;padding:10px 12px 0}}.reason{{padding:8px 12px;background:#f8fafc;font-size:10px;border-bottom:1px solid #e8edf4;word-break:break-word}}.groups{{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:10px 12px}}h3{{font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:#64748b;margin:0 0 7px}}.field{{display:flex;justify-content:space-between;gap:8px;padding:5px 0;border-bottom:1px dashed #e3e9f1;font-size:9px}}.field span{{color:#64748b}}.field b{{text-align:right;word-break:break-word}}footer{{padding:8px 12px;background:#f8fafc;color:#64748b;font-size:8px;word-break:break-all}}.empty{{padding:30px;background:white;border-radius:12px}}@media(max-width:1100px){{.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}@media(max-width:700px){{body{{padding:12px 12px 120px}}.top{{display:block}}.policy{{margin-top:10px}}.grid{{grid-template-columns:1fr}}.groups{{grid-template-columns:1fr}}}}
</style></head><body><div class="top"><div><h1>Order Evidence Dashboard</h1><p>Current runtime truth separated from historical execution evidence · refresh every 5 seconds · generated {generated}</p></div><div class="policy">Read-only · Runtime evidence only · No MT5 initialization · No order send</div></div><div class="notice"><b>Market-closed aware · Truth separation:</b> current runtime state never inherits ORDER_SENT or BLOCKED from stale historical evidence. Historical evidence remains visible for audit.</div><main class="grid">{''.join(cards)}{empty}</main></body></html>'''


def write_order_evidence_dashboard(contract: Mapping[str, Any], output_directory: str | Path = "runtime/dashboard") -> Path:
    path = Path(output_directory) / ORDER_EVIDENCE_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_order_evidence_dashboard(contract), encoding="utf-8")
    return path
