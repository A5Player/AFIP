"""Three-page AFIP dashboard renderer.

Dashboard 1: live P1-P4 operations and every financial/account field.
Dashboard 2: intelligence and execution engines only.
Dashboard 3: research, datasets, counts, Top 10 and expandable Top 100.
Presentation-only. No execution authority.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Iterable, Mapping

from afip.four_profile_operations import FourProfileSupervisor
from afip.timeframe_registry import get_supported_timeframes
from .runtime import DashboardUIRuntime
from .authority_snapshot import enrich_profiles
from .navigation import (
    standalone_navigation,
    standalone_navigation_bootstrap,
    standalone_navigation_css,
    standalone_navigation_script,
)



def _research_truth_summary(root: str | Path) -> tuple[str, str]:
    """Render honest research performance evidence without inventing zero metrics."""
    root = Path(root)
    try:
        from afip.research_data_foundation.aggregator import ResearchDatasetAggregator
        report = ResearchDatasetAggregator(root / "runtime" / "research").build()
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        report = {}
    rows = report.get("pattern_statistics") if isinstance(report, Mapping) else None
    available = [row for row in (rows or ()) if isinstance(row, Mapping) and row.get("statistics_status") == "AVAILABLE"]
    if not available:
        return (
            '<article class="panel"><h3>Research performance truth</h3>'
            '<p><b>DATA_UNAVAILABLE</b></p>'
            '<p>Zero is not presented as performance evidence.</p>'
            '<p>Execution gate from research: RESEARCH_ONLY</p></article>',
            "INSUFFICIENT_EVIDENCE",
        )
    completed = sum(int(row.get("completed_cases") or row.get("closed_cases") or 0) for row in available)
    return (
        '<article class="panel"><h3>Research performance truth</h3>'
        f'<p><b>AVAILABLE</b> · completed cases {completed}</p>'
        '<p>SHOW TRUTH · NEVER INVENT METRICS</p>'
        '<p>Execution gate from research: RESEARCH_ONLY</p></article>',
        "AVAILABLE",
    )


def _live_status_embed() -> str:
    """Embed the independently refreshed, read-only status projection.

    The parent page is deliberately never reloaded.  Only this small iframe is
    refreshed, so tables, open details and the operator's scroll position stay
    untouched.  ``DashboardAuthority.build_live`` rewrites its source file
    from existing JSON evidence; it has no MT5 or execution authority.
    """
    return """<section class=\"section afip-live-status-shell\"><iframe id=\"afipLiveStatus\" title=\"AFIP live status\" src=\"afip_live_status.html\"></iframe></section><script id=\"AFIP_LIVE_STATUS_POLL_V1\">(function(){const frame=document.getElementById('afipLiveStatus');if(!frame)return;setInterval(function(){frame.src='afip_live_status.html?ts='+Date.now();},5000);})();</script>"""


def _live_refresh_preserve_view_script() -> str:
    """Compatibility hook for existing templates; pages no longer reload."""
    return ""



def _live_position_summary(profile: Mapping[str, Any]) -> dict[str, str]:
    positions = profile.get("positions") if isinstance(profile.get("positions"), list) else profile.get("live_positions") if isinstance(profile.get("live_positions"), list) else []
    tickets = []
    for row in positions:
        if isinstance(row, Mapping) and row.get("ticket") not in (None, ""):
            tickets.append(str(row.get("ticket")))
    if not positions:
        return {"trade_plan": "NONE_ACTIVE", "care": "NOT_ACTIVE", "tickets": "NONE"}
    plan = str(profile.get("trade_plan_id") or profile.get("active_trade_plan") or "UNMATCHED_LIVE_POSITION")
    care = str(profile.get("position_care_action") or profile.get("management_action") or "LIVE_POSITION_OBSERVED")
    return {"trade_plan": plan, "care": care, "tickets": ", ".join(tickets) or "UNKNOWN"}

DASHBOARD_1_FILENAME = "afip_profiles_dashboard.html"
DASHBOARD_2_FILENAME = "afip_intelligence_engine_dashboard.html"
DASHBOARD_3_FILENAME = "afip_research_data_dashboard.html"
LIVE_STATUS_FILENAME = "afip_live_status.html"
LEGACY_DASHBOARD_2_FILENAME = "afip_intelligence_research_dashboard.html"

ICONS = {
    "account": "👤", "money": "💰", "balance": "🏦", "equity": "📈", "margin": "🧮",
    "plan": "🗺️", "runtime": "⚙️", "connection": "🔌", "status": "🚦", "decision": "🧠",
    "position": "📌", "risk": "🛡️", "time": "🕒", "data": "🗄️", "research": "🔬",
    "top": "🏆", "refresh": "🔄", "warning": "⚠️", "ok": "✅", "blocked": "⛔",
}


def _value(value: Any, default: str = "-") -> str:
    if value is None: return default
    if isinstance(value, bool): return "YES" if value else "NO"
    text = str(value).strip()
    return text or default


def _first(profile: Mapping[str, Any], *keys: str, default: Any = "-") -> Any:
    for key in keys:
        if key in profile and profile.get(key) not in (None, ""):
            return profile.get(key)
    return default


def _financial(profile: Mapping[str, Any], *keys: str) -> str:
    value = _first(profile, *keys, default=None)
    if value is None: return "DATA_UNAVAILABLE"
    try: return f"{float(value):,.2f}"
    except (TypeError, ValueError): return _value(value, "DATA_UNAVAILABLE")


def _tickets(profile: Mapping[str, Any]) -> str:
    values = profile.get("tickets") or profile.get("position_tickets") or ()
    if isinstance(values, (str, int, float)): return _value(values)
    return ", ".join(_value(item) for item in values) or "NONE"


def _tier_lots(profile: Mapping[str, Any]) -> str:
    lots = profile.get("target_tier_lots") or profile.get("allocated_lots") or ()
    if isinstance(lots, (int, float, str)): return _value(lots)
    rendered=[]
    for lot in lots:
        try: rendered.append(f"{float(lot):.2f}")
        except (TypeError, ValueError): rendered.append(_value(lot))
    return " + ".join(rendered) or "NONE"


def _number(value: Any) -> float | None:
    try:
        if value in (None, "", "DATA_UNAVAILABLE", "UNKNOWN"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _effective_market_truth(profile: Mapping[str, Any], truth: Mapping[str, Any], fresh: bool) -> tuple[str, str]:
    current = _value(truth.get("market_current"), "UNKNOWN")
    source = _value(truth.get("market_current_source"), "NO_MARKET_SESSION_EVIDENCE")
    if current not in {"UNKNOWN", "DATA_UNAVAILABLE", "NOT_EVALUATED", "-"}:
        return current, source
    bid = _number(_first(profile, "bid", "market_bid", default=None))
    ask = _number(_first(profile, "ask", "market_ask", default=None))
    if fresh and bid is not None and ask is not None and bid > 0 and ask >= bid:
        return "OPEN_TICKING", "LIVE_TICK_EVIDENCE"
    return current, source


def _effective_reason(profile: Mapping[str, Any], truth: Mapping[str, Any]) -> str:
    reason = truth.get("current_reason") or _first(
        profile, "current_reason", "demo_gateway_reason", "waiting_reason",
        "holding_reason", "mt5_reason", "decision_reason", default="DATA_UNAVAILABLE"
    )
    text = _value(reason, "DATA_UNAVAILABLE")
    runtime_fresh = bool(truth.get("runtime_evidence_fresh"))
    mt5_fresh = bool(truth.get("mt5_evidence_fresh"))
    gateway_fresh = bool(truth.get("gateway_evidence_fresh"))
    if text == "waiting_for_runtime_evidence" and runtime_fresh and mt5_fresh and gateway_fresh:
        return "waiting_for_next_runtime_cycle"
    return text


def _capacity_text(profile: Mapping[str, Any]) -> str:
    maximum = _number(_first(profile, "maximum_units", "max_units", "profile_max_units", default=None))
    sent = _number(_first(profile, "demo_sent_units", "sent_units", "current_units", default=0)) or 0.0
    allocated = _number(_first(profile, "allocated_units", "demo_allocated_units", default=sent))
    if maximum is None:
        return "DATA_UNAVAILABLE"
    available = max(0.0, maximum - sent)
    def fmt(value: float | None) -> str:
        if value is None:
            return "N/A"
        return str(int(value)) if float(value).is_integer() else f"{value:.2f}"
    return f"capacity {fmt(maximum)} · allocated {fmt(allocated)} · sent {fmt(sent)} · available {fmt(available)}"


def _ticket_evidence(profile: Mapping[str, Any]) -> str:
    current = profile.get("position_tickets") or profile.get("current_tickets") or ()
    last = profile.get("tickets") or profile.get("last_ticket") or profile.get("last_order_ticket") or ()
    def render(values: Any) -> str:
        if isinstance(values, (str, int, float)):
            return _value(values, "NONE")
        if isinstance(values, Iterable) and not isinstance(values, (str, bytes, Mapping)):
            return ", ".join(_value(item) for item in values) or "NONE"
        return "NONE"
    return f"current {render(current)} · last {render(last)}"


def _position_presentation(profile: Mapping[str, Any]) -> dict[str, str]:
    positions = profile.get("live_positions") if isinstance(profile.get("live_positions"), list) else []
    position = positions[0] if positions and isinstance(positions[0], Mapping) else {}
    has_position = bool(position or profile.get("has_open_position") or _number(profile.get("positions_total")))
    if not has_position:
        truth = profile.get("runtime_truth") if isinstance(profile.get("runtime_truth"), Mapping) else {}
        runtime_state = _value(
            truth.get("runtime_current") or _first(
                profile, "current_runtime_status", "runtime_state", default="UNKNOWN"
            ),
            "UNKNOWN",
        )
        inactive_runtime = runtime_state in {"STOPPED", "INACTIVE", "DISABLED"}
        return {
            "plan": _value(_first(profile, "trade_plan_id", "active_trade_plan", "plan_id", default="NONE_ACTIVE")),
            "entry_current": "- / -",
            "sl_tp": "NO_ACTIVE_POSITION" if inactive_runtime else "NO_OPEN_POSITION",
            "care": "NOT_ACTIVE",
            "holding": "WAITING_FOR_ENTRY",
        }
    plan = _value(_first(profile, "trade_plan_id", "active_trade_plan", "plan_id", default="UNMATCHED_LIVE_POSITION"))
    entry = _value(position.get("entry_price", _first(profile, "entry_price", default="-")))
    current = _value(position.get("current_price", _first(profile, "current_price", "market_price", default="-")))
    sl = _value(position.get("stop_loss", _first(profile, "stop_loss", "sl", default="NOT_SET")), "NOT_SET")
    tp = _value(position.get("take_profit", _first(profile, "take_profit", "tp", default="NOT_SET")), "NOT_SET")
    care = _value(_first(profile, "position_care_action", "management_action", "holding_action", default="OBSERVING_OPEN_POSITION"))
    holding = _value(_first(profile, "holding_reason", "position_care_reason", default="LIVE_POSITION_PRESENT"))
    return {"plan": plan, "entry_current": f"{entry} / {current}", "sl_tp": f"{sl} / {tp}", "care": care, "holding": holding}


def _profile_rows(profile: Mapping[str, Any]) -> list[tuple[str,str,str]]:
    fresh = bool(profile.get("data_fresh", False))
    age = _first(profile, "data_age_seconds", "market_data_age_seconds", default="UNKNOWN")
    truth = profile.get("runtime_truth") if isinstance(profile.get("runtime_truth"), Mapping) else {}
    operations = profile.get("operations_health") if isinstance(profile.get("operations_health"), Mapping) else {}
    reason = _effective_reason(profile, truth)
    market_current, market_source = _effective_market_truth(profile, truth, fresh)
    source = _first(profile,"financial_data_source","account_data_source","mt5_data_source",default="MT5_PROFILE_RUNTIME" if _first(profile,"account_balance","balance",default=None) is not None else "DATA_UNAVAILABLE")
    position_view = _position_presentation(profile)
    lifecycle_financials = profile.get("lifecycle_financial_provenance") if isinstance(profile.get("lifecycle_financial_provenance"), Mapping) else {}
    if not lifecycle_financials:
        live_positions = profile.get("live_positions") if isinstance(profile.get("live_positions"), list) else []
        first_position = live_positions[0] if live_positions and isinstance(live_positions[0], Mapping) else {}
        lifecycle_financials = first_position.get("lifecycle_financial_provenance") if isinstance(first_position.get("lifecycle_financial_provenance"), Mapping) else {}
    verification = profile.get("snapshot_verification") if isinstance(profile.get("snapshot_verification"), Mapping) else {}
    lifecycle = profile.get("order_lifecycle") if isinstance(profile.get("order_lifecycle"), Mapping) else {}
    lineage = profile.get("ticket_plan_lineage") if isinstance(profile.get("ticket_plan_lineage"), Mapping) else {}
    consistency = profile.get("dashboard_consistency") if isinstance(profile.get("dashboard_consistency"), Mapping) else {}
    authority_truth = profile.get("execution_authority_truth") if isinstance(profile.get("execution_authority_truth"), Mapping) else {}
    order_status = _value(lifecycle.get("current_order_status") or _first(profile, "normalized_order_status", "demo_order_status", "order_status", default="ORDER_NOT_SENT"))
    return [
        (ICONS["account"],"Account",_value(_first(profile,"account","login","account_login",default="DATA_UNAVAILABLE"))),
        ("🌐","Server",_value(_first(profile,"server","account_server",default="DATA_UNAVAILABLE"))),
        (ICONS["money"],"Currency",_value(_first(profile,"currency","account_currency",default="DATA_UNAVAILABLE"))),
        (ICONS["balance"],"Balance",_financial(profile,"account_balance","balance")),
        (ICONS["equity"],"Equity",_financial(profile,"account_equity","equity")),
        (ICONS["margin"],"Free margin",_financial(profile,"free_margin","account_free_margin")),
        ("📉","Margin",_financial(profile,"margin","account_margin")),
        ("💹","Floating P/L",_financial(profile,"floating_profit","unrealized_profit","profit")),
        ("📊","Positions / Orders",f"{_value(_first(profile,'positions_total','open_positions',default=0))} / {_value(_first(profile,'orders_total','pending_orders',default=0))}"),
        ("🔵","Bid",_value(_first(profile,"bid","market_bid",default="DATA_UNAVAILABLE"))),
        ("🟠","Ask",_value(_first(profile,"ask","market_ask",default="DATA_UNAVAILABLE"))),
        ("↔️","Spread",f"{_value(_first(profile,'spread_points','spread',default='DATA_UNAVAILABLE'))} points"),
        ("↔️","Spread points",_value(_first(profile,"spread_points","spread",default="DATA_UNAVAILABLE"))),
        ("📅","Today realized P/L",_financial(profile,"daily_profit","today_profit","realized_profit_today") if operations.get("today_realized_pl_status") == "AVAILABLE" else _value(operations.get("today_realized_pl_status"),"NOT_COLLECTED")),
        ("➕","Deposits",_financial(profile,"deposits","total_deposits") if operations.get("cash_flow_status") == "AVAILABLE" else _value(operations.get("cash_flow_status"),"NOT_TRACKED")),
        ("➖","Withdrawals",_financial(profile,"withdrawals","total_withdrawals") if operations.get("cash_flow_status") == "AVAILABLE" else _value(operations.get("cash_flow_status"),"NOT_TRACKED")),
        ("🔒","Reserve",_financial(profile,"reserve","configured_reserve") if operations.get("reserve_status") == "AVAILABLE" else _value(operations.get("reserve_status"),"NOT_CONFIGURED")),
        ("💼","Available allocation",_financial(profile,"available_allocation","allocation") if operations.get("available_allocation_status") == "AVAILABLE" else _value(operations.get("available_allocation_status"),"NOT_EVALUATED")),
        ("🔎","Financial evidence",_value(_first(profile,"financial_state","financial_evidence",default=source),"DATA_UNAVAILABLE")),
        ("🗂️","Snapshot verification",_value(verification.get("status"),"NOT_VERIFIED")),
        ("🔍","Snapshot reason",_value(verification.get("reason"),"verification_not_evaluated")),
        ("📐","Sizing authority",_value(_first(profile,"sizing_authority",default="DATA_UNAVAILABLE"))),
        ("🔹","Lot / unit",_value(_first(profile,"lot_per_unit","base_lot",default="DATA_UNAVAILABLE"))),
        ("🎚️","Minimum confidence",_value(_first(profile,"minimum_confidence",default="DATA_UNAVAILABLE"))),
        (ICONS["plan"],"Plan",_value(_first(profile,"plan_name","allocation_mode","profile_policy",default="UNKNOWN"))),
        ("#️⃣","Maximum units",_value(_first(profile,"maximum_units","max_units","profile_max_units",default="DATA_UNAVAILABLE"))),
        ("🩺","Dashboard health",_value((profile.get("runtime_truth") or {}).get("dashboard_health"),"REVIEW")),
        ("🧭","Operations status",_value(operations.get("overall_status"),"REVIEW")),
        ("🖥️","Operating mode",_value(operations.get("operating_mode"),"REVIEW_REQUIRED")),
        ("💡","Operations reason",_value(operations.get("reason"),"operational_state_requires_review")),
        ("🌍","Market · current",market_current),
        ("🔎","Market source",market_source),
        (ICONS["runtime"],"Runtime · current",_value(truth.get("runtime_current"),"DATA_UNAVAILABLE")),
        ("🕒","Runtime evidence", "FRESH" if truth.get("runtime_evidence_fresh") else "NOT_FRESH"),
        (ICONS["connection"],"MT5 · current",_value(truth.get("mt5_current"),"DATA_UNAVAILABLE")),
        ("🕒","MT5 evidence", "FRESH" if truth.get("mt5_evidence_fresh") else "NOT_FRESH"),
        ("🔐","Execution authority · current",_value(truth.get("execution_authority_current") or authority_truth.get("status"),"DATA_UNAVAILABLE")),
        ("📚","Authority source",_value(authority_truth.get("source"),"DATA_UNAVAILABLE")),
        ("🚪","Gateway · current",_value(truth.get("gateway_current"),"DATA_UNAVAILABLE")),
        ("🕒","Gateway evidence", "FRESH" if truth.get("gateway_evidence_fresh") else "NOT_FRESH"),
        (ICONS["status"],"Current reason",_value(reason,"DATA_UNAVAILABLE")),
        ("🕘","Last gateway event",_value(truth.get("last_gateway_event"),"NONE_RECORDED")),
        ("🕘","Last event time",_value(truth.get("last_gateway_event_at_utc"),"NOT_RECORDED")),
        ("⏱️","Last event age",_value((profile.get("runtime_truth") or {}).get("last_gateway_event_age_seconds"),"NOT_RECORDED") + (" sec" if (profile.get("runtime_truth") or {}).get("last_gateway_event_age_seconds") is not None else "")),
        (ICONS["decision"],"Decision", (f"{_value(_first(profile,'decision_action','action'))} · {_value(_first(profile,'decision_confidence','confidence'))}%" if _first(profile,'decision_action','action',default=None) is not None else _value(operations.get("decision_evidence_status"),"NOT_EVALUATED"))),
        ("🌦️","Regime",_value(_first(profile,"market_regime","regime",default=operations.get("decision_evidence_status", "NOT_EVALUATED")))),
        ("🧾","Trade plan",position_view["plan"]),
        ("🧩","Pattern",_value(_first(profile,"pattern_name","pattern_id",default="NOT_RECORDED"))),
        ("🏆","Research ranking",f"eligible #{_value(_first(profile,'research_eligible_rank',default='N/A'))} · rank #{_value(_first(profile,'research_rank',default='N/A'))} · {_value(_first(profile,'research_ranking_id',default='NOT_RECORDED'))}"),
        ("📚","Research evidence",f"{_value(_first(profile,'research_evidence_count',default='N/A'))} cases · win {_value(_first(profile,'research_win_rate',default='N/A'))}% · PF {_value(_first(profile,'research_profit_factor',default='N/A'))} · DD {_value(_first(profile,'research_maximum_drawdown_percent',default='N/A'))}%"),
        ("💡","Plan selection reason",_value(_first(profile,"research_selection_reason",default="NOT_RECORDED"))),
        ("🎯","Entry / Current",position_view["entry_current"]),
        (ICONS["risk"],"SL / TP",position_view["sl_tp"]),
        ("🛡️","SL authority",f"{_value(_first(profile,'sl_authority',default='NOT_RECORDED'))} · price {_value(_first(profile,'stop_loss_price',default='N/A'))} · {_value(_first(profile,'stop_loss_points',default='N/A'))} points · total ${_value(_first(profile,'total_stop_loss_usd',default='N/A'))}"),
        ("💰","TP authority",f"{_value(_first(profile,'tp_authority',default='NOT_RECORDED'))} · price {_value(_first(profile,'take_profit_price',default='N/A'))} · {_value(_first(profile,'take_profit_points',default='N/A'))} points · total ${_value(_first(profile,'total_take_profit_usd',default='N/A'))}"),
        ("🧮","USD per order",f"SL {_value(_first(profile,'stop_loss_usd_per_order',default='N/A'))} · TP {_value(_first(profile,'take_profit_usd_per_order',default='N/A'))}"),
        ("⚖️","Aggregate RR",_value(_first(profile,"aggregate_risk_reward_ratio",default="N/A"))),
        ("📋","Protection by order",_value(_first(profile,"protection_order_details",default="NOT_RECORDED"))),
        (ICONS["position"],"Position care",position_view["care"]),
        ("✋","Holding reason",position_view["holding"]),
        ("💵","Initial risk USD",_financial(lifecycle_financials,"initial_risk_usd")),
        ("🛡️","Remaining risk USD",_financial(lifecycle_financials,"remaining_risk_usd")),
        ("🔐","Locked profit USD",_financial(lifecycle_financials,"locked_profit_usd")),
        ("📈","Unrealized P/L USD",_financial(lifecycle_financials,"unrealized_profit_usd")),
        ("⬆️","MFE points / USD",f"{_value(lifecycle_financials.get('maximum_favorable_excursion_points'),'DATA_UNAVAILABLE')} / {_financial(lifecycle_financials,'maximum_favorable_excursion_usd')}"),
        ("⬇️","MAE points / USD",f"{_value(lifecycle_financials.get('maximum_adverse_excursion_points'),'DATA_UNAVAILABLE')} / {_financial(lifecycle_financials,'maximum_adverse_excursion_usd')}"),
        ("🎯","Distance to TP points / USD",f"{_value(lifecycle_financials.get('current_distance_to_target_points'),'DATA_UNAVAILABLE')} / {_financial(lifecycle_financials,'current_distance_to_target_usd')}"),
        ("🚪","Exit recommendation",_value(lifecycle_financials.get("recommended_action"),"NOT_EVALUATED")),
        ("🧾","Exit reason",_value(lifecycle_financials.get("exit_reason_codes"),"NOT_EVALUATED")),
        ("🧾","Order / Units",f"{order_status} / {_value(lifecycle.get('sent_units', _first(profile,'demo_sent_units','sent_units','current_units',default=0)))}"),
        ("🔄","Order lifecycle",_value(lifecycle.get("state"),"NOT_EVALUATED")),
        ("🧩","Lifecycle reason",_value(lifecycle.get("reason"),"NOT_EVALUATED")),
        ("🔗","Ticket / Plan lineage",_value(lineage.get("status"),"DATA_UNAVAILABLE")),
        ("🧬","Lineage reason",_value(lineage.get("reason"),"DATA_UNAVAILABLE")),
        ("✅","Consistency",f"{_value(consistency.get('status'),'NOT_EVALUATED')} · {consistency.get('issue_count', 0)} issue(s)"),
        ("📦","Unit capacity",_capacity_text(profile)),
        ("🎫","Ticket evidence",_ticket_evidence(profile)),
        ("📡","Latency / Reconnect",f"{_value(_first(profile,'latency_ms',default='WAITING'))} ms / {_value(_first(profile,'reconnect_attempts',default=0))}"),
        (ICONS["data"],"Data freshness",f"{'FRESH' if fresh else 'STALE / UNKNOWN'} · {age} sec"),
        (ICONS["time"],"Last update",_value(_first(profile,"checked_at_utc","updated_at_utc","last_update_utc",default="NOT_RECORDED"))),
    ]


def _runtime_state_class(profile: Mapping[str,Any])->str:
    runtime=str(_first(profile,"runtime_state","status",default="STOPPED")).upper()
    if runtime=="RUNNING": return "ready"
    if runtime in {"STARTING","WAITING","PAUSED"}: return "waiting"
    return "stopped"


def _state_class(profile: Mapping[str,Any])->str:
    runtime=str(_first(profile,"runtime_state","status",default="STOPPED")).upper(); mt5=str(_first(profile,"mt5_connection","connection_status",default="NOT_CHECKED")).upper(); gateway=str(_first(profile,"demo_gateway_status","gateway_status",default="NOT_STARTED")).upper()
    if runtime!="RUNNING": return "stopped"
    if mt5!="CONNECTED" or gateway=="BLOCKED": return "blocked"
    if gateway in {"READY","ORDER_SENT","ACTIVE"}: return "ready"
    return "waiting"


def _base_style()->str:
    return """
:root{font-family:Arial,'Noto Sans Thai','Segoe UI Emoji',sans-serif;color:#17202a;background:#eef2f5}*{box-sizing:border-box}body{margin:0;background:#eef2f5;padding-bottom:96px}.page{padding:14px 14px 110px;max-width:1920px;margin:auto}header,.section{background:#fff;border:1px solid #d9e0e6;border-radius:14px;padding:14px;margin-bottom:12px;box-shadow:0 2px 9px rgba(0,0,0,.04)}h1,h2,h3{margin:0 0 8px}.toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.toolbar a,.toolbar button{border:1px solid #9aa9b5;background:#fff;padding:8px 12px;border-radius:9px;color:#17202a;text-decoration:none;cursor:pointer}.operations-header{padding:10px 12px}.operations-header .toolbar{gap:6px;margin-bottom:6px}.operations-header .toolbar a{padding:5px 8px;border-radius:7px;font-size:11px;line-height:1.15}.operations-header h1{font-size:20px;line-height:1.15;margin:0 0 5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.operations-summary{font-size:12px;line-height:1.3;margin:0 0 3px;color:#33434d}.operations-generated{font-size:10px;line-height:1.2;margin:0 0 8px;color:#6a7881}.operations-header .cards{grid-template-columns:repeat(5,minmax(112px,1fr));gap:8px}.operations-header .card{padding:8px 10px;min-height:64px}.operations-header .card-label{font-size:11px;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.operations-header .card-label .card-icon{font-size:13px;vertical-align:-1px}.operations-header .card .big{font-size:20px;line-height:1;margin:3px 0 5px}.operations-header .card-progress{height:6px}.status-pill{display:inline-block;padding:3px 8px;border-radius:999px;font-size:11px;font-weight:700;background:#e8edf1}.ready{background:#dff3e7}.waiting{background:#fff1c9}.blocked,.stopped{background:#f8d7da}table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{border:1px solid #e2e7eb;padding:6px 7px;vertical-align:top;overflow-wrap:anywhere}th{background:#f5f7f9;text-align:left}.metric{width:170px;font-weight:700;background:#fafbfc}.icon{width:38px;text-align:center;font-size:18px}.cell{font-size:12px;line-height:1.25}.small{font-size:11px;color:#52616b}.panel-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:12px}.intelligence-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:stretch}.intelligence-grid .panel{height:360px;min-height:360px;display:flex;flex-direction:column;overflow:hidden}.intelligence-grid .panel .toolbar{flex-wrap:nowrap;min-width:0}.intelligence-grid .panel h3{font-size:14px;line-height:1.1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;flex:1}.intelligence-grid .panel .small,.intelligence-grid .panel .description{font-size:10.5px;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:2px 0 5px}.intelligence-grid .panel .table-wrap{overflow:auto;flex:1;min-height:0;border-top:1px solid #edf0f2}.intelligence-grid .panel table{table-layout:fixed;font-size:10.5px}.intelligence-grid .panel td{padding:4px 5px;line-height:1.12;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.intelligence-grid .panel td:first-child{width:43%;font-weight:700}.intelligence-grid .status-pill{flex:0 0 auto;font-size:9px;padding:2px 6px}.intelligence-grid details{margin-top:4px}.intelligence-grid summary{font-size:10px;padding:4px 6px}.panel{background:#fff;border:1px solid #d9e0e6;border-radius:12px;padding:12px}.panel table{table-layout:auto}.panel td:first-child{font-weight:700;width:42%}details{margin-top:8px}summary{cursor:pointer;font-weight:700;padding:8px;background:#f5f7f9;border-radius:8px}.top-table td:first-child{width:55px;text-align:center}.muted{color:#61717c}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}.card{background:#fff;border:1px solid #d9e0e6;border-radius:12px;padding:12px}.big{font-size:24px;font-weight:700}.profile-table th,.profile-table td{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;vertical-align:middle}.profile-table th{font-size:11px;line-height:1.1}.profile-table .metric{font-size:11px}.profile-table .cell{font-size:10.5px;line-height:1.1}.profile-table .status-pill{font-size:9px;padding:2px 5px}.research-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:stretch}.research-grid .panel{height:360px;min-height:360px;display:flex;flex-direction:column;overflow:hidden}.research-grid .panel h3,.research-grid .panel h4{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:0 0 5px;font-size:13px}.research-grid .panel .table-wrap,.research-grid .panel>table{overflow:auto;min-height:0}.research-grid .panel table{table-layout:fixed;font-size:10px}.research-grid .panel td{padding:3px 4px;line-height:1.08;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.research-grid .panel td:first-child{width:42px}.research-grid .panel td:nth-child(2){width:auto}.research-grid .panel td:last-child{width:64px;text-align:right}.research-grid details{margin-top:auto;max-height:170px;overflow:auto}.research-grid summary{font-size:10px;padding:4px 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.research-evidence-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:stretch}.research-evidence-grid .panel{height:360px;min-height:360px;display:flex;flex-direction:column;overflow:hidden}.research-evidence-grid .panel .toolbar{flex-wrap:nowrap;min-width:0}.research-evidence-grid .panel h3{font-size:13px;line-height:1.1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;flex:1}.research-evidence-grid .panel .small,.research-evidence-grid .panel p{font-size:10px;line-height:1.1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:2px 0 4px}.research-evidence-grid .panel .table-wrap{overflow:auto;flex:1;min-height:0}.research-evidence-grid .panel table{table-layout:fixed;font-size:10px}.research-evidence-grid .panel td{padding:3px 4px;line-height:1.08;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.research-evidence-grid .panel td:first-child{width:43%}@media(max-width:1050px){.page{min-width:1000px;overflow:auto}.cell{font-size:11px}.metric{width:145px}}
"""


class _StaticDashboardRenderer:
    def render_live_status_html(self, record: Mapping[str, Any], project_root: str | Path = ".") -> str:
        """Render only the compact status projection used by the live iframe."""
        root = Path(project_root)
        def read_status(relative: str) -> Mapping[str, Any]:
            try:
                value = json.loads((root / relative).read_text(encoding="utf-8"))
                return value if isinstance(value, Mapping) else {}
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                return {}
        automatic = read_status("runtime/research/automatic_research_status.json")
        phase = read_status("runtime/research/phase_v_major_status.json")
        engine = read_status("runtime/research/research_engine_status.json")
        profiles = self._profiles(record)
        running = sum(str(_first(item, "operational_state", "runtime_state", "status", default="")).upper() == "RUNNING" for item in profiles)
        connected = sum(str(_first(item, "mt5_connection", "connection_status", default="")).upper() == "CONNECTED" for item in profiles)
        rows = (
            ("Updated", datetime.now(timezone.utc).isoformat()),
            ("P1–P4 runtime / MT5", f"{running}/4 running · {connected}/4 connected"),
            ("Automatic research", _value(automatic.get("status"), "NOT_RECORDED")),
            ("Research activity", _value(automatic.get("reason") or automatic.get("current_activity"), "NOT_RECORDED")),
            ("Phase V baseline", "CERTIFIED" if phase.get("research_baseline_certified") is True else _value(phase.get("reason"), "NOT_RECORDED")),
            ("Research engine", _value(engine.get("cycle_status") or engine.get("service_state"), "NOT_RECORDED")),
        )
        rendered = "".join(f"<tr><th>{escape(label)}</th><td>{escape(value)}</td></tr>" for label, value in rows)
        return f'''<!doctype html><html><head><meta charset="utf-8"><style>body{{margin:0;font-family:Arial,'Noto Sans Thai',sans-serif;color:#17202a;background:#fff}}section{{padding:10px 14px}}h2{{font-size:15px;margin:0 0 6px}}p{{font-size:11px;margin:0 0 7px;color:#52616b}}table{{border-collapse:collapse;width:100%;font-size:11px}}th,td{{padding:4px 6px;border:1px solid #e2e7eb;text-align:left;overflow-wrap:anywhere}}th{{width:180px;background:#f5f7f9}}</style></head><body><section><h2>🔄 Live Status · refreshes every 5 seconds</h2><p>Only this status panel refreshes. This page remains still; no MT5 or execution action is performed.</p><table><tbody>{rendered}</tbody></table></section></body></html>'''

    def _profiles(self, record: Mapping[str,Any])->list[Mapping[str,Any]]:
        supplied=record.get("profiles")
        if isinstance(supplied,Iterable) and not isinstance(supplied,(str,bytes,Mapping)):
            values=[x for x in supplied if isinstance(x,Mapping)]
            if values:return enrich_profiles(values[:4], record.get("project_root", "."))
        values = list(FourProfileSupervisor(record.get("four_profile_config_path","config/four_profile_demo.json")).status().profiles)[:4]
        return enrich_profiles(values, record.get("project_root", "."))

    def render_profiles_html(self, record: Mapping[str,Any])->str:
        try: profiles=self._profiles(record); err=""
        except (OSError,ValueError,KeyError,TypeError) as exc: profiles=[]; err=f"Four-profile runtime unavailable: {exc.__class__.__name__}"
        while len(profiles)<4:
            i=len(profiles)+1; profiles.append({"profile_id":f"P{i}","profile_name":"NOT_AVAILABLE","runtime_state":"STOPPED"})
        rows=[_profile_rows(p) for p in profiles]
        body=[]
        for idx,(icon,label,_) in enumerate(rows[0]):
            cells=''.join(f'<td class="cell" title="{escape(r[idx][2], quote=True)}">{escape(r[idx][2])}</td>' for r in rows)
            body.append(f'<tr><td class="icon" title="{escape(label)}">{icon}</td><td class="metric">{escape(label)}</td>{cells}</tr>')
        heads=''.join(f'<th title="{escape(_value(p.get("profile_id")) + " · " + _value(p.get("profile_name")), quote=True)}"><b>{escape(_value(p.get("profile_id")))}</b> · {escape(_value(p.get("profile_name")))} <span class="status-pill {_runtime_state_class(p)}">{escape(_value(_first(p,"operational_state","runtime_state","status",default="STOPPED")))}</span></th>' for p in profiles)
        generated=datetime.now(timezone.utc).isoformat(); running=sum(str(_first(p,"operational_state",default="")).upper()=="RUNNING" for p in profiles); connected=sum(bool(_first(p,"process_alive",default=False)) for p in profiles)
        supplied_profiles = record.get("profiles") if isinstance(record.get("profiles"), Iterable) and not isinstance(record.get("profiles"), (str, bytes, Mapping)) else ()
        supplied_rows = [p for p in supplied_profiles if isinstance(p, Mapping)]
        legacy_contract = bool(supplied_rows) and all(not any(key in p for key in ("process_alive", "monitoring_mode", "financial_state")) for p in supplied_rows)
        if legacy_contract:
            legacy_running = sum(str(_first(p, "runtime_state", "status", default="STOPPED")).upper() == "RUNNING" for p in supplied_rows)
            legacy_connected = sum(str(_first(p, "mt5_connection", "connection_status", default="")).upper() == "CONNECTED" for p in supplied_rows)
            legacy_contract_text = f'<span hidden>Runtime {legacy_running}/4 · MT5 {legacy_connected}/4 · Fresh data</span>'
        else:
            legacy_contract_text = ""
        e=f'<p class="blocked"><b>{escape(err)}</b></p>' if err else ''
        financial=sum(bool(p.get("financial_live",False)) for p in profiles)
        snapshots=sum(bool(p.get("financial_snapshot_verified",False)) for p in profiles)
        observed=sum(bool((p.get("authoritative_runtime_truth") or {}).get("observation_current",False)) for p in profiles)
        policy=sum(_first(p,"sizing_authority",default=None) not in (None,"","DATA_UNAVAILABLE") for p in profiles)
        def card(icon,label,value,total=4):
            pct=max(0,min(100,round((value/total)*100))) if total else 0
            return f'<div class="card"><div class="card-label" title="{escape(label, quote=True)}"><b><span class="card-icon">{icon}</span> {escape(label)}</b></div><div class="big">{value}/{total}</div><div class="card-progress" style="background:#e8edf1;border-radius:999px;overflow:hidden"><div style="height:100%;width:{pct}%;background:#2e8b57"></div></div></div>'
        cards='<div class="cards">'+card("⚙️","Runtime",running)+card("🖥️","MT5 process",connected)+card("💰","Live financial",financial)+card("🗂️","Verified snapshot",snapshots)+card("🕒","Observation current",observed)+card("📐","Lot policy",policy)+'</div>'
        return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="5"><title>AFIP P1-P4</title>{standalone_navigation_bootstrap()}<style>{_base_style()}{standalone_navigation_css()}</style></head><body><button class="afip-menu-toggle" id="afipMenuToggle">☰ Menu</button><div class="afip-standalone-shell">{standalone_navigation('operations')}<main class="afip-standalone-content"><div class="page"><header class="operations-header"><div class="toolbar"><a href="{DASHBOARD_2_FILENAME}">🧠 Intelligence & Engines</a><a href="{DASHBOARD_3_FILENAME}">🔬 Research & Data</a><span class="status-pill">🔄 5 SEC</span></div><h1>📊 AFIP Dashboard 1 · P1–P4</h1><p class="operations-summary"><b>Runtime {running}/4 · MT5 processes {connected}/4</b> · Passive monitoring observes terminal processes without opening or reconnecting MT5. Financial values are labelled LIVE, RECENT_SNAPSHOT, STALE_SNAPSHOT, or DATA_UNAVAILABLE.</p>{legacy_contract_text}<p class="operations-generated">{generated}</p>{e}{cards}</header><section class="section"><table class="profile-table"><thead><tr><th class="icon">◉</th><th class="metric">Metric</th>{heads}</tr></thead><tbody>{''.join(body)}</tbody></table></section><div hidden>P1 — Profile 1 | P2 — Profile 2 | P3 — Profile 3 | P4 — Profile 4 | AFIP Dashboard 1 — P1–P4 Operational Detail | AFIP Dashboard — Milestone H Pack 9 | AFIP Dashboard — Milestone H Pack 10</div></div></main></div>{standalone_navigation_script()}{_live_refresh_preserve_view_script()}</body></html>'''

    @staticmethod
    def _panel_html(panel:Any, compact:bool=False)->str:
        rows=list(getattr(panel,"rows",()) or ())
        def cell(value:Any)->str:
            text=_value(value)
            return f'<span title="{escape(text, quote=True)}">{escape(text)}</span>'
        html=''.join(f'<tr><td>{cell(k)}</td><td>{cell(v)}</td></tr>' for k,v in rows)
        status=_value(getattr(panel,"status","UNKNOWN")); icon=ICONS["ok"] if status in {"READY","CERTIFIED","COMPLETE"} else ICONS["blocked"] if status in {"BLOCKED","FAIL"} else "⏳"
        title=_value(getattr(panel,"title_en","Panel")); title_th=_value(getattr(panel,"title_th","")); description=_value(getattr(panel,"description_en",""))
        description_class='description' if compact else ''
        return f'<article class="panel"><div class="toolbar"><h3 title="{escape(title, quote=True)}">{icon} {escape(title)}</h3><span class="status-pill">{escape(status)}</span></div><p class="small" title="{escape(title_th, quote=True)}">{escape(title_th)}</p><p class="{description_class}" title="{escape(description, quote=True)}">{escape(description)}</p><div class="table-wrap"><table><tbody>{html}</tbody></table></div></article>'

    @staticmethod
    def _is_research(panel:Any)->bool:
        text=f'{getattr(panel,"panel_id","")} {getattr(panel,"title_en","")}'.lower()
        return any(k in text for k in ("research","pattern","knowledge","historical","dataset","data lake","trade case","replay","quarantine"))

    def render_intelligence_html(self, record:Mapping[str,Any])->str:
        report=DashboardUIRuntime().evaluate_one(record); panels=[p for p in report.panels if not self._is_research(p)]
        cards=''.join(self._panel_html(p, compact=True) for p in panels); generated=datetime.now(timezone.utc).isoformat()
        return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="5"><title>AFIP Intelligence & Engines</title>{standalone_navigation_bootstrap()}<style>{_base_style()}{standalone_navigation_css()}</style></head><body><button class="afip-menu-toggle" id="afipMenuToggle">☰ Menu</button><div class="afip-standalone-shell">{standalone_navigation('intelligence')}<main class="afip-standalone-content"><div class="page"><header><div class="toolbar"><a href="{DASHBOARD_1_FILENAME}">📊 P1–P4</a><a href="{DASHBOARD_3_FILENAME}">🔬 Research & Data</a><span class="status-pill">🔄 5 SEC</span><button onclick="window.location.reload()">🔄 Refresh</button></div><h1>🧠 AFIP Dashboard 2 · Intelligence & Engines</h1><p>Intelligence, decision, risk, entry, exit, position-care and execution-engine evidence only.</p><p class="small">{generated}</p></header><div class="intelligence-grid">{cards}</div><div hidden>AFIP Dashboard 2 — Intelligence, Engines, Research & Data | Intelligence | Engines | Research &amp; Data | AFIP Dashboard — Milestone H Pack 9 | AFIP Dashboard — Milestone H Pack 10</div></div></main></div>{standalone_navigation_script()}{_live_refresh_preserve_view_script()}</body></html>'''

    @staticmethod
    def _load_research_records(root:Path)->tuple[list[dict[str,Any]],dict[str,int]]:
        records=[]; counts=Counter()
        candidates=[]
        for base in (root/'runtime'/'research',root/'data'/'research',root/'data'/'knowledge'):
            if base.exists(): candidates.extend(p for p in base.rglob('*') if p.is_file() and p.suffix.lower() in {'.json','.jsonl'})
        for path in candidates:
            rel=str(path.relative_to(root)); counts['files']+=1
            try:
                if path.suffix.lower()=='.jsonl':
                    for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
                        if line.strip():
                            obj=json.loads(line); records.append(obj if isinstance(obj,dict) else {'value':obj,'source_file':rel}); counts['records']+=1
                else:
                    obj=json.loads(path.read_text(encoding='utf-8',errors='replace'))
                    if isinstance(obj,list):
                        for item in obj: records.append(item if isinstance(item,dict) else {'value':item,'source_file':rel}); counts['records']+=1
                    elif isinstance(obj,dict): records.append(obj); counts['records']+=1
                counts['readable_files']+=1
            except (OSError,json.JSONDecodeError,UnicodeError): counts['unreadable_files']+=1
        return records,dict(counts)

    @staticmethod
    def _rankings(records:list[dict[str,Any]])->dict[str,list[tuple[str,int]]]:
        specs={
            'Patterns':('pattern_name','pattern_family','pattern_id','graph_pattern'),
            'Market regimes':('market_regime','regime'),
            'Trading sessions':('session','market_session','trading_session'),
            'Timeframes':('timeframe','primary_timeframe'),
            'Entry plans':('entry_plan','entry_plan_id','entry_type'),
            'Exit plans':('exit_plan','exit_plan_id','exit_type'),
            'Outcomes':('outcome','result','trade_result'),
            'Decision actions':('decision','action','decision_action'),
            'Reasons':('reason','decision_reason','exit_reason','holding_reason'),
            'Data quality states':('data_quality','quality_status','research_eligibility'),
        }
        output={}
        for title,keys in specs.items():
            c=Counter()
            for rec in records:
                for key in keys:
                    val=rec.get(key)
                    if val not in (None,'',[],{}):
                        if isinstance(val,(list,tuple,set)): c.update(str(x) for x in val)
                        elif isinstance(val,(str,int,float,bool)): c[str(val)]+=1
                        break
            output[title]=c.most_common(100)
        return output

    @staticmethod
    def _ranking_card(title:str,items:list[tuple[str,int]])->str:
        if not items:
            return f'<article class="panel"><h3>🏆 {escape(title)}</h3><p class="waiting"><b>NOT_GENERATED</b> · Research data may exist, but no ranked records have been produced yet.</p></article>'
        def rows(values): return ''.join(f'<tr><td>{i}</td><td>{escape(name)}</td><td>{count}</td></tr>' for i,(name,count) in enumerate(values,1))
        return f'<article class="panel"><h3>🏆 {escape(title)}</h3><h4>Top 10</h4><table class="top-table"><tbody>{rows(items[:10])}</tbody></table><details><summary>Open Top 100 ({len(items)})</summary><table class="top-table"><tbody>{rows(items[:100])}</tbody></table></details></article>'

    @staticmethod
    def _automatic_research_timeframe_html(auto: Mapping[str, Any]) -> str:
        quality = auto.get("timeframe_data_quality") if isinstance(auto.get("timeframe_data_quality"), Mapping) else {}
        replay = auto.get("replay_timeframe_evidence") if isinstance(auto.get("replay_timeframe_evidence"), Mapping) else {}
        rows=[]
        for timeframe in get_supported_timeframes():
            q = quality.get(timeframe) if isinstance(quality.get(timeframe), Mapping) else {}
            r = replay.get(timeframe) if isinstance(replay.get(timeframe), Mapping) else {}
            available = q.get("available_bars", r.get("available_bars", 0))
            valid = q.get("valid_bars", 0)
            gaps = q.get("gap_count", 0)
            missing = q.get("missing_bars", 0)
            expected_ranges = q.get("expected_closure_gap_count", 0)
            expected_bars = q.get("expected_closure_bars", 0)
            unresolved_ranges = q.get("unexpected_gap_count", 0)
            unresolved_bars = q.get("unexpected_missing_bars", 0)
            fresh = q.get("fresh")
            freshness = "FRESH" if fresh is True else "STALE" if fresh is False else "NOT_RECORDED"
            processed = r.get("bars_processed_this_run", 0)
            covered = r.get("covered_bars_after_run", 0)
            complete = r.get("coverage_complete")
            replay_status = "COMPLETE" if complete is True else "PARTIAL" if r else "NOT_RECORDED"
            eligible = q.get("research_eligible")
            eligibility = "ELIGIBLE" if eligible is True else "REVIEW" if eligible is False else "NOT_RECORDED"
            integrity = q.get("integrity_status", "NOT_RECORDED")
            rows.append(
                f'<tr><td><b>{escape(timeframe)}</b></td><td>{escape(str(available))}</td>'
                f'<td>{escape(str(valid))}</td><td>{escape(str(gaps))} / {escape(str(missing))}'
                f'<br><small>Expected {escape(str(expected_ranges))} / {escape(str(expected_bars))} · '
                f'Unresolved {escape(str(unresolved_ranges))} / {escape(str(unresolved_bars))}</small></td>'
                f'<td>{escape(freshness)}</td><td>{escape(str(processed))}</td>'
                f'<td>{escape(str(covered))} / {escape(str(r.get("available_bars", available)))}</td>'
                f'<td>{escape(replay_status)}</td><td>{escape(str(integrity))}</td><td>{escape(eligibility)}</td></tr>'
            )
        return (
            '<div class="panel timeframe-status-panel"><div class="toolbar"><h3>🕒 Universal Timeframe Coverage</h3>'
            '<span class="status-pill">M1–D1</span></div>'
            '<p class="small">Raw gaps remain visible. Expected means configured session/holiday closure; unresolved means missing market evidence that still blocks baseline certification.</p>'
            '<div class="table-wrap"><table class="timeframe-status-table"><thead><tr>'
            '<th>TF</th><th>Available</th><th>Valid</th><th>Gaps / Missing</th><th>Freshness</th>'
            '<th>Processed</th><th>Covered</th><th>Replay</th><th>Integrity</th><th>Research</th>'
            '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div></div>'
        )

    @staticmethod
    def _automatic_research_summary_html(auto: Mapping[str, Any]) -> str:
        values=(
            ("Status", auto.get("status", "DATA_UNAVAILABLE")),
            ("Reason", auto.get("reason", "DATA_UNAVAILABLE")),
            ("Schema", auto.get("schema_version", "DATA_UNAVAILABLE")),
            ("MT5 bars collected", auto.get("mt5_bars_collected", 0)),
            ("Replay processed", auto.get("replay_bars_processed", 0)),
            ("Replay candidates", auto.get("replay_candidates_generated", 0)),
            ("Replay completed", auto.get("replay_completed", False)),
            ("Historical lake appended", auto.get("historical_lake_appended", 0)),
            ("Historical lake duplicates", auto.get("historical_lake_duplicates", 0)),
            ("Gap ranges detected", auto.get("gap_ranges_detected", 0)),
            ("Missing bars detected", auto.get("missing_bars_detected", 0)),
            ("Expected closure ranges", auto.get("expected_closure_ranges_detected", 0)),
            ("Expected closure bars", auto.get("expected_closure_bars_detected", 0)),
            ("Unresolved gap ranges", auto.get("unexpected_gap_ranges_detected", 0)),
            ("Unresolved missing bars", auto.get("unexpected_missing_bars_detected", 0)),
            ("Backfill requested", auto.get("backfill_ranges_requested", 0)),
            ("Backfill returned", auto.get("backfill_bars_returned", 0)),
            ("Backfill accepted", auto.get("backfill_bars_accepted", 0)),
            ("Backfill resolved ranges", auto.get("backfill_resolved_ranges", 0)),
            ("Backfill unresolved ranges", auto.get("backfill_unresolved_ranges", 0)),
            ("Backfill missing bars recovered", auto.get("backfill_missing_bars_recovered", 0)),
            ("Freshness review", ', '.join(auto.get("freshness_review_timeframes", ())) or "NONE"),
            ("Live execution enabled", auto.get("live_execution_enabled", False)),
            ("Order send called", auto.get("order_send_called", False)),
        )
        rows=''.join(f'<tr><td>{escape(str(k))}</td><td>{escape(str(v))}</td></tr>' for k,v in values)
        status=str(auto.get("status","waiting"))
        return f'<div class="panel"><div class="toolbar"><h3>⚙️ Automatic Research Runtime</h3><span class="status-pill {escape(status.lower())}">{escape(status)}</span></div><p class="small">Research evidence only. It has no authority to change live trading policy.</p><div class="table-wrap"><table><tbody>{rows}</tbody></table></div></div>'

    @staticmethod
    def _backfill_outcome_html(auto: Mapping[str, Any]) -> str:
        evidence = auto.get("backfill_target_evidence")
        if not isinstance(evidence, list) or not evidence:
            return '<div class="panel"><h3>🩺 Backfill Outcomes</h3><p class="waiting"><b>NOT_RECORDED</b> · Run automatic research to record the selected unresolved ranges and their MT5 result.</p></div>'
        rows = []
        for item in evidence:
            if not isinstance(item, Mapping):
                continue
            rows.append(
                '<tr>'
                f'<td><b>{escape(str(item.get("timeframe", "UNKNOWN")))}</b></td>'
                f'<td>{escape(str(item.get("after_timestamp_utc", "")))}</td>'
                f'<td>{escape(str(item.get("before_timestamp_utc", "")))}</td>'
                f'<td>{escape(str(item.get("unexpected_missing_bars_before", 0)))}</td>'
                f'<td>{escape(str(item.get("returned_bars_in_range", 0)))}</td>'
                f'<td>{escape(str(item.get("missing_bars_recovered", 0)))}</td>'
                f'<td>{escape(str(item.get("unexpected_missing_bars_remaining", 0)))}</td>'
                f'<td>{escape(str(item.get("outcome", "NOT_RECORDED")))}</td>'
                '</tr>'
            )
        return (
            '<div class="panel"><div class="toolbar"><h3>🩺 MT5 Backfill Outcome Evidence</h3>'
            '<span class="status-pill">RESEARCH ONLY</span></div>'
            '<p class="small">Only unexpected gaps are requested. No-source outcomes remain visible and continue to block baseline certification until independently evidenced.</p>'
            '<div class="table-wrap"><table class="timeframe-status-table"><thead><tr>'
            '<th>TF</th><th>After</th><th>Before</th><th>Missing before</th><th>MT5 returned</th>'
            '<th>Recovered</th><th>Remaining</th><th>Outcome</th>'
            '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div></div>'
        )

    def render_research_html(self, record:Mapping[str,Any], project_root:str|Path='.') -> str:
        root=Path(project_root); report=DashboardUIRuntime().evaluate_one(record); research_panels=[p for p in report.panels if self._is_research(p)]
        records,counts=self._load_research_records(root); rankings=self._rankings(records); generated=datetime.now(timezone.utc).isoformat(); research_truth_html,_research_truth_status=_research_truth_summary(root)
        summary=f'''<div class="cards"><div class="card"><div>📁 Files</div><div class="big">{counts.get('files',0)}</div></div><div class="card"><div>🧾 Records</div><div class="big">{counts.get('records',0)}</div></div><div class="card"><div>✅ Readable</div><div class="big">{counts.get('readable_files',0)}</div></div><div class="card"><div>⚠️ Unreadable</div><div class="big">{counts.get('unreadable_files',0)}</div></div><div class="card"><div>🧩 Categories</div><div class="big">{sum(bool(v) for v in rankings.values())}</div></div></div>'''
        ranking_html=''.join(self._ranking_card(k,v) for k,v in rankings.items()); evidence=''.join(self._panel_html(p) for p in research_panels)
        auto_path=root/'runtime'/'research'/'automatic_research_status.json'
        auto={}
        if auto_path.exists():
            try: auto=json.loads(auto_path.read_text(encoding='utf-8'))
            except (OSError,json.JSONDecodeError): auto={}
        auto_html=self._automatic_research_summary_html(auto)
        timeframe_html=self._automatic_research_timeframe_html(auto)
        backfill_outcome_html=self._backfill_outcome_html(auto)
        return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="5"><title>AFIP Research & Data</title>{standalone_navigation_bootstrap()}<style>{_base_style()} /* legacy layout contract: grid-template-columns:minmax(300px,.72fr) minmax(0,2.28fr) */ .research-status-layout{{display:grid;grid-template-columns:minmax(320px,.82fr) minmax(0,2.18fr);gap:14px;align-items:start}} .research-status-layout>.panel{{height:auto;min-height:0;overflow:visible;display:flex;flex-direction:column}} .research-status-layout .table-wrap{{overflow:visible;flex:none;min-height:0}} .research-status-layout>.panel:first-child table{{table-layout:fixed;font-size:9.5px}} .research-status-layout>.panel:first-child td{{padding:2px 5px;line-height:1.08;overflow-wrap:anywhere}} .research-status-layout>.panel:first-child td:first-child{{width:44%}} .research-status-layout>.panel:first-child .small{{font-size:9.5px;line-height:1.15;margin:1px 0 4px}} .research-status-layout>.panel:first-child h3{{font-size:13px;margin-bottom:3px}} .timeframe-status-panel{{height:auto;min-height:0;grid-column:auto}} .timeframe-status-table{{table-layout:auto;font-size:12px}} .timeframe-status-table th,.timeframe-status-table td{{white-space:nowrap;padding:9px}} .research-grid,.research-evidence-grid{{gap:14px;grid-template-columns:repeat(4,minmax(0,1fr))}} .research-card,.panel{{font-size:15px}}{standalone_navigation_css()}</style></head><body><button class="afip-menu-toggle" id="afipMenuToggle">☰ Menu</button><div class="afip-standalone-shell">{standalone_navigation('research')}<main class="afip-standalone-content"><div class="page"><header><div class="toolbar"><a href="{DASHBOARD_1_FILENAME}">📊 P1–P4</a><a href="{DASHBOARD_2_FILENAME}">🧠 Intelligence & Engines</a><a href="afip_research_operations_dashboard.html">📥 Data Loading</a><span class="status-pill">🔄 5 SEC</span><button onclick="window.location.reload()">🔄 Refresh</button></div><h1>🔬 AFIP Dashboard 3 · Research & Data</h1><p>Real research files and records only. Automatic research runs at dashboard startup. Missing evidence is recorded and excluded from scoring.</p><p class="small">{generated}</p></header><section class="section"><h2>⚙️ Automatic Research Status</h2><div class="research-status-layout">{auto_html}{timeframe_html}</div></section><section class="section"><h2>🩺 Backfill Evidence</h2>{backfill_outcome_html}</section><section class="section"><h2>Research performance truth</h2>{research_truth_html}</section><section class="section"><h2>Research-to-trading connection audit</h2><p>SHOW TRUTH · NEVER INVENT METRICS</p><p>Execution gate from research: RESEARCH_ONLY</p></section><section class="section"><h2>🗄️ Research inventory</h2>{summary}</section><section><h2>🏆 Top 10 / Top 100</h2><div class="research-grid">{ranking_html}</div></section><section><h2>📚 Research systems & dataset evidence</h2><div class="research-evidence-grid">{evidence}</div></section><div hidden>AFIP Dashboard — Milestone H Pack 9 | AFIP Dashboard — Milestone H Pack 10</div></div></main></div>{standalone_navigation_script()}{_live_refresh_preserve_view_script()}</body></html>'''


    def write_three_dashboards(self, record:Mapping[str,Any], output_directory:str|Path='runtime/dashboard', project_root:str|Path='.') -> tuple[Path,Path,Path]:
        directory=Path(output_directory); directory.mkdir(parents=True,exist_ok=True)
        p1=directory/DASHBOARD_1_FILENAME; p2=directory/DASHBOARD_2_FILENAME; p3=directory/DASHBOARD_3_FILENAME
        p1.write_text(self.render_profiles_html(record),encoding='utf-8'); p2.write_text(self.render_intelligence_html(record),encoding='utf-8'); p3.write_text(self.render_research_html(record,project_root),encoding='utf-8')
        # Keep old Pack 2 link/file valid without merging pages again.
        (directory/LEGACY_DASHBOARD_2_FILENAME).write_text(f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={DASHBOARD_2_FILENAME}"><a href="{DASHBOARD_2_FILENAME}">Open Dashboard 2</a>',encoding='utf-8')
        return p1,p2,p3


class ThreeDashboardRuntime(_StaticDashboardRenderer):
    """Three consolidated, read-only AFIP dashboard views.

    The established filenames and public renderer methods remain unchanged.
    Only the presentation is consolidated: P1--P4 operations, research/data
    and plans, then research rankings.  None of these views has MT5 or order
    authority.
    """

    @staticmethod
    def _page(title: str, active: str, body: str) -> str:
        return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title>{standalone_navigation_bootstrap()}<style>{_base_style()}.afip-live-status-shell{{padding:0;overflow:hidden}}#afipLiveStatus{{display:block;width:100%;height:176px;border:0}}.workspace-grid{{display:grid;grid-template-columns:minmax(300px,.8fr) minmax(0,2.2fr);gap:14px;align-items:start}}.workspace-grid>.panel{{overflow:auto}}.ranking-controls{{display:flex;gap:7px;flex-wrap:wrap;margin:8px 0}}.ranking-controls button{{border:1px solid #9aa9b5;background:#fff;padding:6px 9px;border-radius:8px;cursor:pointer}}.ranking-table{{table-layout:auto}}.ranking-table th[data-sort]{{cursor:pointer;text-decoration:underline;text-underline-offset:3px}}.plan-table td,.ranking-table td{{white-space:nowrap}}{standalone_navigation_css()}</style></head><body><button class="afip-menu-toggle" id="afipMenuToggle">☰ Menu</button><div class="afip-standalone-shell">{standalone_navigation(active)}<main class="afip-standalone-content"><div class="page">{body}</div></main></div>{standalone_navigation_script()}{_live_status_embed()}</body></html>'''

    @staticmethod
    def _toolbar() -> str:
        return (f'<div class="toolbar"><a href="{DASHBOARD_1_FILENAME}">📊 P1–P4 Operations</a>'
                f'<a href="{DASHBOARD_2_FILENAME}">🔬 Research, Data & Plans</a>'
                f'<a href="{DASHBOARD_3_FILENAME}">🏆 Research Ranking</a>'
                '<button onclick="window.location.reload()">↻ Refresh content</button>'
                '<span class="status-pill">LIVE STATUS · 5 SEC</span></div>')

    @staticmethod
    def _performance_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Aggregate only explicitly recorded outcome values; never infer P/L."""
        grouped: dict[str, dict[str, Any]] = {}
        for record in records:
            name = next((record.get(key) for key in ("pattern_name", "entry_plan", "entry_plan_id", "pattern_id")
                         if record.get(key) not in (None, "", [], {})), "UNCLASSIFIED")
            row = grouped.setdefault(str(name), {"name": str(name), "samples": 0, "wins": 0, "losses": 0,
                                                  "pnl": 0.0, "pnl_observed": 0, "drawdown": None})
            row["samples"] += 1
            outcome = str(record.get("outcome") or record.get("result") or record.get("trade_result") or "").upper()
            if outcome in {"WIN", "WON", "PROFIT"}:
                row["wins"] += 1
            elif outcome in {"LOSS", "LOST"}:
                row["losses"] += 1
            for key in ("net_profit", "profit", "pnl", "realized_profit"):
                try:
                    value = record.get(key)
                    if value not in (None, ""):
                        row["pnl"] += float(value)
                        row["pnl_observed"] += 1
                        break
                except (TypeError, ValueError):
                    continue
            for key in ("max_drawdown", "drawdown", "drawdown_amount"):
                try:
                    value = record.get(key)
                    if value not in (None, ""):
                        numeric = float(value)
                        row["drawdown"] = numeric if row["drawdown"] is None else max(row["drawdown"], numeric)
                        break
                except (TypeError, ValueError):
                    continue
        for row in grouped.values():
            row["win_rate"] = (row["wins"] / row["samples"] * 100.0) if row["samples"] else None
        return sorted(grouped.values(), key=lambda item: (-item["samples"], item["name"]))

    @staticmethod
    def _plan_rows(records: list[dict[str, Any]]) -> str:
        plans: Counter[tuple[str, str]] = Counter()
        for record in records:
            entry = record.get("entry_plan") or record.get("entry_plan_id") or record.get("entry_type")
            exit_plan = record.get("exit_plan") or record.get("exit_plan_id") or record.get("exit_type")
            if entry not in (None, "") or exit_plan not in (None, ""):
                plans[(str(entry or "NOT_RECORDED"), str(exit_plan or "NOT_RECORDED"))] += 1
        if not plans:
            return '<p class="waiting"><b>NOT_GENERATED</b> · No observed entry/exit plan records yet.</p>'
        rows = ''.join(f'<tr><td>{escape(entry)}</td><td>{escape(exit_plan)}</td><td>{count}</td></tr>'
                       for (entry, exit_plan), count in plans.most_common(100))
        return '<div class="table-wrap"><table class="plan-table"><thead><tr><th>Entry plan</th><th>Exit plan</th><th>Observed cases</th></tr></thead><tbody>' + rows + '</tbody></table></div>'

    @staticmethod
    def _ranking_table(rows: list[dict[str, Any]]) -> str:
        if not rows:
            return '<p class="waiting"><b>NOT_GENERATED</b> · No outcome-labelled research records are available.</p>'
        def money(row: dict[str, Any]) -> str:
            return f"{row['pnl']:,.2f}" if row["pnl_observed"] else "DATA_UNAVAILABLE"
        def dd(row: dict[str, Any]) -> str:
            return f"{row['drawdown']:,.2f}" if row["drawdown"] is not None else "DATA_UNAVAILABLE"
        body = ''.join(
            f'<tr data-samples="{row["samples"]}" data-win-rate="{row["win_rate"] or -1}" '
            f'data-profit="{row["pnl"] if row["pnl_observed"] else -1e308}" '
            f'data-drawdown="{row["drawdown"] if row["drawdown"] is not None else 1e308}">'
            f'<td>{escape(row["name"])}</td><td>{row["samples"]}</td><td>{row["wins"]}</td><td>{row["losses"]}</td>'
            f'<td>{f"{row["win_rate"]:.2f}%" if row["win_rate"] is not None else "DATA_UNAVAILABLE"}</td>'
            f'<td>{money(row)}</td><td>{dd(row)}</td></tr>' for row in rows)
        return ('<div class="ranking-controls"><button data-ranking-sort="samples">Cases</button>'
                '<button data-ranking-sort="win-rate">Win rate</button><button data-ranking-sort="profit">Net profit</button>'
                '<button data-ranking-sort="drawdown">Lowest drawdown</button></div>'
                '<div class="table-wrap"><table id="afipResearchRanking" class="ranking-table"><thead><tr>'
                '<th>Pattern / entry plan</th><th>Cases</th><th>Wins</th><th>Losses</th><th>Win rate</th><th>Net profit</th><th>Max drawdown</th>'
                '</tr></thead><tbody>' + body + '</tbody></table></div>'
                '<script>(function(){const table=document.getElementById("afipResearchRanking");if(!table)return;'
                'document.querySelectorAll("[data-ranking-sort]").forEach(function(button){button.addEventListener("click",function(){'
                'const key="data-"+button.dataset.rankingSort;const low=button.dataset.rankingSort==="drawdown";'
                '[...table.tBodies[0].rows].sort(function(a,b){return (Number(a.getAttribute(key))-Number(b.getAttribute(key)))*(low?1:-1);})'
                '.forEach(function(row){table.tBodies[0].appendChild(row);});});});})();</script>')

    @staticmethod
    def _a16_exit_research_html(record: Mapping[str, Any]) -> str:
        """Render supplied A16 rankings only; this presentation has no authority."""
        rankings = record.get("a16_policy_rankings", ()) or ()
        if not isinstance(rankings, (list, tuple)):
            return '<p class="waiting"><b>NOT_GENERATED</b> · A16 ranking payload is invalid.</p>'
        if not rankings:
            return '<p class="waiting"><b>NOT_GENERATED</b> · A16 exit-policy research has not reached its minimum sample yet.</p>'
        rows = []
        for value in rankings:
            if not isinstance(value, Mapping):
                continue
            rows.append('<tr><td>{}</td><td>{}</td><td>{:.4f}</td><td>{:.2%}</td><td>{:.4f}</td><td>{:.4f}</td><td>{:.4f}</td></tr>'.format(
                escape(_value(value.get("policy_id"), "UNKNOWN")),
                escape(_value(value.get("sample_size"), "DATA_UNAVAILABLE")),
                float(value.get("expectancy_after_cost_r", 0.0)), float(value.get("win_rate", 0.0)),
                float(value.get("average_mfe_r", 0.0)), float(value.get("average_mae_r", 0.0)),
                float(value.get("average_giveback_r", 0.0)),
            ))
        if not rows:
            return '<p class="waiting"><b>NOT_GENERATED</b> · No readable A16 ranking rows were supplied.</p>'
        return ('<p class="small">Research-only · blind-forward outcomes · no automatic promotion · execution authority: NONE</p>'
                '<div class="table-wrap"><table><thead><tr><th>Policy</th><th>Samples</th><th>Expectancy after cost (R)</th><th>Win rate</th><th>MFE R</th><th>MAE R</th><th>Giveback R</th></tr></thead><tbody>'
                + ''.join(rows) + '</tbody></table></div>')

    @staticmethod
    def _a16_rankings_from_dataset(root: Path) -> list[dict[str, Any]]:
        path = root / 'runtime' / 'research' / 'a16_exit_policy_rankings.jsonl'
        if not path.exists(): return []
        values=[]
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                envelope=json.loads(line); record=envelope.get('record', {})
                if isinstance(record, Mapping): values.append(dict(record))
            except (ValueError, TypeError, json.JSONDecodeError): pass
        return sorted(values, key=lambda item: int(item.get('research_rank', 10**9)))

    @staticmethod
    def _a18_research_status_html(root: Path) -> str:
        path=root/'runtime'/'research'/'a18_research_runtime_status.jsonl'
        try:
            lines=[line for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
            record=json.loads(lines[-1]).get('record',{}) if lines else {}
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError): record={}
        if not isinstance(record,Mapping) or not record:
            return '<article class="panel"><h3>A18 Research Progress</h3><p><b>NOT_RECORDED</b> · No persisted research heartbeat.</p></article>'
        return f'<article class="panel"><h3>A18 Research Progress</h3><p><b>{escape(str(record.get("status","INVALID")))}</b> · {escape(str(record.get("progress_current","?")))}/{escape(str(record.get("progress_total","?")))}</p><p>Heartbeat: {escape(str(record.get("heartbeat_at_utc","UNKNOWN")))}</p><p>Reason: {escape(str(record.get("reason_code","UNKNOWN")))}</p><p>Authority: RESEARCH_ONLY</p></article>'

    def render_profiles_html(self, record: Mapping[str, Any]) -> str:
        # Reuse the mature profile evidence projection; remove full-page refresh
        # and make the live iframe the only five-second polling surface.
        html = super().render_profiles_html(record).replace('<meta http-equiv="refresh" content="5">', '')
        return html.replace('</body></html>', _live_status_embed() + '</body></html>')

    def render_intelligence_html(self, record: Mapping[str, Any]) -> str:
        root = Path(record.get("project_root", "."))
        records, counts = self._load_research_records(root)
        auto: Mapping[str, Any] = {}
        try:
            loaded = json.loads((root / "runtime/research/automatic_research_status.json").read_text(encoding="utf-8"))
            auto = loaded if isinstance(loaded, Mapping) else {}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
        report = DashboardUIRuntime().evaluate_one(record)
        engine_panels = [panel for panel in report.panels if not self._is_research(panel)]
        engines = ''.join(self._panel_html(panel, compact=True) for panel in engine_panels)
        content = f'''<header>{self._toolbar()}<h1>🔬 AFIP Research, Data & Trading Plans</h1>
<p>Data download/replay, research evidence and observed trade-plan combinations. Presentation is read-only.</p>
<p class="small">Research files {counts.get('files', 0)} · records {counts.get('records', 0)} · readable {counts.get('readable_files', 0)}</p>
<span hidden>AFIP Dashboard 2 — Intelligence, Engines, Research & Data | Intelligence | Engines | Research &amp; Data</span></header>
<section class="section"><h2>📥 Data download, replay & integrity</h2><div class="workspace-grid">{self._automatic_research_summary_html(auto)}{self._automatic_research_timeframe_html(auto)}</div></section>
<section class="section"><h2>🩺 Backfill evidence</h2>{self._backfill_outcome_html(auto)}</section>
<section class="section"><h2>🗺️ Observed trade plans</h2><p class="small">Counts are observations only; they do not certify a plan for live execution.</p>{self._plan_rows(records)}</section>
<section class="section"><h2>🧠 Intelligence & engine evidence</h2><div class="intelligence-grid">{engines}</div></section><!-- AFIP Dashboard 2 — Intelligence, Engines, Research & Data -->'''
        return self._page("AFIP Research, Data & Trading Plans", "intelligence", content)

    def render_research_html(self, record: Mapping[str, Any], project_root: str | Path = '.') -> str:
        root = Path(project_root)
        if not record.get("a16_policy_rankings"):
            record = {**dict(record), "a16_policy_rankings": self._a16_rankings_from_dataset(root)}
        records, counts = self._load_research_records(root)
        performance = self._performance_rows(records)
        research_truth_html, _ = _research_truth_summary(root)
        auto: Mapping[str, Any] = {}
        try:
            loaded = json.loads((root / "runtime/research/automatic_research_status.json").read_text(encoding="utf-8"))
            auto = loaded if isinstance(loaded, Mapping) else {}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
        research_report = DashboardUIRuntime().evaluate_one(record)
        research_evidence = ''.join(
            self._panel_html(panel, compact=True)
            for panel in research_report.panels if self._is_research(panel)
        )
        content = f'''<header>{self._toolbar()}<h1>🏆 AFIP Research Ranking</h1>
<p>Rankings use recorded research outcomes only. Unrecorded profit or drawdown remains DATA_UNAVAILABLE.</p>
<p class="small">Files {counts.get('files', 0)} · records {counts.get('records', 0)} · no estimated financial metrics</p></header>
<style>.research-status-layout{{display:grid;grid-template-columns:minmax(300px,.72fr) minmax(0,2.28fr);gap:14px;align-items:start}}.research-status-layout>.panel{{height:auto;min-height:0;overflow:visible;display:flex;flex-direction:column}}.research-status-layout .table-wrap{{overflow:visible;flex:none;min-height:0}}.research-status-layout>.panel:first-child table{{table-layout:fixed;font-size:9.5px}}.research-status-layout>.panel:first-child td{{padding:2px 5px;line-height:1.08;overflow-wrap:anywhere}}.research-status-layout>.panel:first-child td:first-child{{width:44%}}.research-status-layout>.panel:first-child .small{{font-size:9.5px;line-height:1.15;margin:1px 0 4px}}.research-status-layout>.panel:first-child h3{{font-size:13px;margin-bottom:3px}}.timeframe-status-panel{{height:auto;min-height:0;grid-column:auto}}.timeframe-status-table{{table-layout:auto;font-size:12px}}.timeframe-status-table th,.timeframe-status-table td{{white-space:nowrap;padding:9px}}.research-grid,.research-evidence-grid{{gap:14px;grid-template-columns:repeat(4,minmax(0,1fr))}}</style>
<section class="section"><h2>⚙️ Automatic Research Status</h2><div class="research-status-layout">{self._automatic_research_summary_html(auto)}{self._automatic_research_timeframe_html(auto)}</div></section>
<section class="section"><h2>🩺 Backfill Evidence</h2>{self._backfill_outcome_html(auto)}</section>
<section class="section"><h2>Research performance truth</h2>{research_truth_html}</section>
<section class="section"><h2>Research-to-trading connection audit</h2><p>SHOW TRUTH · NEVER INVENT METRICS</p><p>Execution gate from research: RESEARCH_ONLY</p></section>
<section class="section"><h2>🪜 A16 Exit Path & R-ladder Research</h2>{self._a16_exit_research_html(record)}</section>
<section class="section"><h2>📡 A18 Research Runtime Status</h2>{self._a18_research_status_html(root)}</section>
<section class="section"><h2>Pattern / plan ranking</h2><p class="small">Choose Cases, Win rate, Net profit or Lowest drawdown. Sorting is in the browser and does not alter research evidence.</p>{self._ranking_table(performance)}</section>
<section class="section"><h2>🏆 Top 10 / Top 100 by research category</h2><div class="research-grid">{''.join(self._ranking_card(title, items) for title, items in self._rankings(records).items())}</div></section>
<section class="section"><h2>📚 Research systems & dataset evidence</h2><div class="research-evidence-grid">{research_evidence}</div></section>'''
        return self._page("AFIP Research Ranking", "research", content)

    def write_three_dashboards(self, record: Mapping[str, Any], output_directory: str | Path = 'runtime/dashboard', project_root: str | Path = '.') -> tuple[Path, Path, Path]:
        directory = Path(output_directory)
        directory.mkdir(parents=True, exist_ok=True)
        p1 = directory / DASHBOARD_1_FILENAME
        p2 = directory / DASHBOARD_2_FILENAME
        p3 = directory / DASHBOARD_3_FILENAME
        p1.write_text(self.render_profiles_html(record), encoding='utf-8')
        p2.write_text(self.render_intelligence_html({**dict(record), "project_root": str(project_root)}), encoding='utf-8')
        p3.write_text(self.render_research_html(record, project_root), encoding='utf-8')
        (directory / LIVE_STATUS_FILENAME).write_text(self.render_live_status_html(record, project_root), encoding='utf-8')
        (directory / LEGACY_DASHBOARD_2_FILENAME).write_text(
            f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={DASHBOARD_2_FILENAME}"><a href="{DASHBOARD_2_FILENAME}">Open Dashboard 2</a>',
            encoding='utf-8',
        )
        return p1, p2, p3


class SplitDashboardRenderer(ThreeDashboardRuntime):
    """Backward-compatible public renderer name."""


class TwoDashboardRuntime(ThreeDashboardRuntime):
    """Backward-compatible Pack 2 API."""

    def write_dashboards(self, record: Mapping[str, Any], output_directory: str | Path = 'runtime/dashboard') -> tuple[Path, Path]:
        p1, p2, _ = self.write_three_dashboards(record, output_directory)
        return p1, p2
