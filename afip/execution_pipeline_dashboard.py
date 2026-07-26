"""Read-only AFIP V1 live execution pipeline dashboard.

Builds explainable per-profile pipeline evidence from the dashboard data
contract.  It never initializes MT5, recalculates authority, or sends orders.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Mapping, Sequence

PIPELINE_SCHEMA_VERSION = "AFIP_V1_EXECUTION_PIPELINE_DASHBOARD_V2"
PIPELINE_FILENAME = "afip_execution_pipeline_dashboard.html"

STAGES: tuple[tuple[str, str], ...] = (
    ("market_feed", "Market Feed"),
    ("market_regime", "Market Regime"),
    ("pattern_recognition", "Pattern Recognition"),
    ("multi_timeframe", "Multi-Timeframe Analysis"),
    ("confidence", "Confidence"),
    ("capital_authority", "Capital Authority"),
    ("lot_authority", "Lot Authority"),
    ("risk_authority", "Risk Authority"),
    ("sl_authority", "SL Authority"),
    ("tp_authority", "TP Authority"),
    ("trading_cost", "Spread / Trading Cost"),
    ("execution_permission", "Execution Permission"),
    ("mt5_order_check", "MT5 Order Check"),
    ("mt5_order_send", "MT5 Order Send"),
)

_ALIASES: dict[str, tuple[str, ...]] = {
    "market_feed": ("market_feed", "market_data", "market_data_source", "data_source"),
    "market_regime": ("market_regime", "regime", "market_regime_status"),
    "pattern_recognition": ("pattern_recognition", "pattern", "pattern_intelligence", "pattern_status"),
    "multi_timeframe": ("multi_timeframe", "multi_timeframe_confluence", "mtf", "mtf_status"),
    "confidence": ("confidence", "confidence_calibration", "confidence_status"),
    "capital_authority": ("capital_authority", "capital_status", "capital_approval"),
    "lot_authority": ("lot_authority", "lot_status", "position_sizing", "approved_lot"),
    "risk_authority": ("risk_authority", "risk_status", "risk_approval"),
    "sl_authority": ("sl_authority", "stop_loss_authority", "sl_status"),
    "tp_authority": ("tp_authority", "take_profit_authority", "tp_status"),
    "trading_cost": ("trading_cost", "trading_cost_authority", "spread_check", "trading_cost_status"),
    "execution_permission": ("execution_permission", "execution_authority", "gateway_status", "order_readiness"),
    "mt5_order_check": ("mt5_order_check", "order_check", "order_check_called"),
    "mt5_order_send": ("mt5_order_send", "order_send", "order_send_called", "order_status"),
}

_STATUS_WORDS = {
    "PASS": "PASS", "READY": "PASS", "APPROVED": "PASS", "ALLOWED": "PASS",
    "CONNECTED": "PASS", "OPEN": "PASS", "ORDER_SENT": "PASS", "TRUE": "PASS",
    "WAIT": "WAITING", "WAITING": "WAITING", "PENDING": "WAITING", "HOLD": "WAITING",
    "NO_SIGNAL": "WAITING", "ORDER_NOT_SENT": "WAITING", "FALSE": "WAITING",
    "BLOCK": "BLOCKED", "BLOCKED": "BLOCKED", "REJECTED": "BLOCKED", "DENIED": "BLOCKED",
    "FAILED": "FAILED", "FAIL": "FAILED", "ERROR": "FAILED", "DISCONNECTED": "FAILED",
    "UNKNOWN": "DATA_UNAVAILABLE", "NONE": "DATA_UNAVAILABLE", "": "DATA_UNAVAILABLE",
}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first(mapping: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def _normalize_status(value: Any) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "WAITING"
    if isinstance(value, Mapping):
        value = _first(value, ("status", "state", "result", "allowed", "approved", "ready"))
    text = str(value if value is not None else "").strip().upper().replace(" ", "_")
    if text in _STATUS_WORDS:
        return _STATUS_WORDS[text]
    if any(word in text for word in ("BLOCK", "REJECT", "DENY", "INSUFFICIENT", "TOO_HIGH")):
        return "BLOCKED"
    if any(word in text for word in ("ERROR", "FAIL", "DISCONNECT", "INVALID")):
        return "FAILED"
    if any(word in text for word in ("PASS", "READY", "APPROV", "ALLOW", "CONNECTED", "SENT")):
        return "PASS"
    if any(word in text for word in ("WAIT", "PENDING", "HOLD", "COOLDOWN", "NO_ORDER")):
        return "WAITING"
    return "DATA_UNAVAILABLE"


def _detail(value: Any) -> str:
    if isinstance(value, Mapping):
        for key in ("reason", "value", "decision", "status", "state", "result", "score", "confidence"):
            if value.get(key) is not None:
                return str(value[key])
        return "runtime evidence available"
    if value is None:
        return "DATA_UNAVAILABLE"
    return str(value)


def _pipeline_sources(profile: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    return (
        _mapping(profile.get("decision_pipeline")),
        _mapping(profile.get("intelligence_snapshot")),
        _mapping(profile.get("execution_trace")),
        _mapping(profile.get("authority_snapshot")),
        profile,
    )


def _evidence_semantics(profile: Mapping[str, Any]) -> dict[str, Any]:
    metadata = _mapping(profile.get("source_metadata"))
    execution_meta = _mapping(metadata.get("execution_state"))
    status_meta = _mapping(metadata.get("profile_status"))
    if not metadata:
        return {"mode": "LIVE", "freshness": str(profile.get("data_status", "DATA_UNAVAILABLE")),
                "age_seconds": profile.get("data_age_seconds"), "reason": None}
    execution_fresh = bool(execution_meta.get("fresh"))
    status_fresh = bool(status_meta.get("fresh"))
    runtime_state = str(profile.get("runtime_state", profile.get("status", "STOPPED"))).upper()
    runtime_running = runtime_state in {"RUNNING", "STARTING", "READY", "ACTIVE"}
    age = execution_meta.get("age_seconds")
    if age is None:
        age = status_meta.get("age_seconds")
    if not runtime_running:
        return {"mode": "INACTIVE", "freshness": "CURRENT_IDLE", "age_seconds": age,
                "reason": "runtime_not_currently_running"}
    if not execution_fresh:
        return {"mode": "HISTORICAL", "freshness": "STALE", "age_seconds": age,
                "reason": "execution_evidence_stale"}
    return {"mode": "LIVE", "freshness": "FRESH" if status_fresh or execution_fresh else "STALE",
            "age_seconds": age, "reason": None}


def build_profile_pipeline(profile: Mapping[str, Any]) -> dict[str, Any]:
    sources = _pipeline_sources(profile)
    stages: list[dict[str, Any]] = []
    first_block: str | None = None
    for stage_id, label in STAGES:
        value = None
        source_name = "DATA_UNAVAILABLE"
        for source in sources:
            value = _first(source, _ALIASES[stage_id])
            if value is not None:
                source_name = "runtime execution evidence"
                break
        status = _normalize_status(value)
        if first_block is None and status in {"BLOCKED", "FAILED"}:
            first_block = stage_id
        stages.append({
            "stage_id": stage_id,
            "label": label,
            "status": status,
            "detail": _detail(value),
            "source": source_name,
        })

    semantics = _evidence_semantics(profile)
    reason = _first(profile, ("gateway_reason", "waiting_reason", "reason", "trading_block_reason"))
    if semantics["mode"] != "LIVE":
        reason = semantics["reason"]
    trace_id = _first(profile, ("execution_trace_id", "trace_id", "decision_trace_id"))
    current = first_block
    if current is None:
        waiting = next((s["stage_id"] for s in stages if s["status"] == "WAITING"), None)
        current = waiting or next((s["stage_id"] for s in stages if s["status"] == "DATA_UNAVAILABLE"), None)
    return {
        "profile_id": str(profile.get("profile_id", "UNKNOWN")),
        "profile_name": str(profile.get("profile_name", profile.get("name", ""))),
        "data_status": str(semantics["freshness"]),
        "data_age_seconds": semantics["age_seconds"],
        "evidence_mode": semantics["mode"],
        "trace_id": str(trace_id or "DATA_UNAVAILABLE"),
        "overall_status": ("INACTIVE" if semantics["mode"] == "INACTIVE" else "HISTORICAL" if semantics["mode"] == "HISTORICAL" else str(profile.get("gateway_status", profile.get("runtime_state", profile.get("status", "DATA_UNAVAILABLE"))))),
        "reason": str(reason or "DATA_UNAVAILABLE"),
        "current_stage": current or "COMPLETE",
        "stages": stages,
    }


def attach_execution_pipelines(contract: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(contract)
    profiles = []
    pipelines = []
    for item in contract.get("profiles", []):
        if not isinstance(item, Mapping):
            continue
        row = dict(item)
        pipeline = build_profile_pipeline(row)
        row["execution_pipeline"] = pipeline
        profiles.append(row)
        pipelines.append(pipeline)
    result["profiles"] = profiles
    result["execution_pipelines"] = pipelines
    result["execution_pipeline_schema_version"] = PIPELINE_SCHEMA_VERSION
    return result


def render_execution_pipeline_dashboard(contract: Mapping[str, Any]) -> str:
    pipelines = contract.get("execution_pipelines", [])
    generated = escape(str(contract.get("generated_at_utc", datetime.now(timezone.utc).isoformat())))
    cards: list[str] = []
    for pipe in pipelines:
        if not isinstance(pipe, Mapping):
            continue
        evidence_mode = str(pipe.get("evidence_mode", "UNKNOWN")).upper()
        stage_rows: list[str] = []
        for stage in pipe.get("stages", []):
            if not isinstance(stage, Mapping):
                continue
            historical_status = str(stage.get("status", "DATA_UNAVAILABLE"))
            historical_detail = str(stage.get("detail", "DATA_UNAVAILABLE"))
            if evidence_mode in {"HISTORICAL", "INACTIVE"}:
                display_status = "NOT_EVALUATED"
                display_class = "not_evaluated"
                detail = f"Last evidence: {historical_status} · {historical_detail}"
            else:
                display_status = historical_status
                display_class = historical_status.lower()
                detail = historical_detail
            stage_rows.append(
                f'<div class="stage {escape(display_class)}"><span class="dot"></span>'
                f'<div><strong>{escape(str(stage["label"]))}</strong><small>{escape(detail)}</small></div>'
                f'<b>{escape(display_status)}</b></div>'
            )
        stage_html = "".join(stage_rows)
        age = pipe.get("data_age_seconds")
        age_text = "NOT_RECORDED" if age is None else f"{escape(str(age))} sec"
        cards.append(
            f'<section class="card"><header><div><h2>{escape(str(pipe.get("profile_id")))} · {escape(str(pipe.get("profile_name")))}</h2>'
            f'<p>Trace: {escape(str(pipe.get("trace_id")))}</p></div><span class="badge">{escape(str(pipe.get("data_status")))}</span></header>'
            f'<div class="summary"><span>State <b>{escape(str(pipe.get("overall_status")))}</b></span>'
            f'<span>Stage <b>{escape(str(pipe.get("current_stage")))}</b></span>'
            f'<span>Evidence <b>{escape(str(pipe.get("evidence_mode", "UNKNOWN")))}</b></span>'
            f'<span>Age <b>{age_text}</b></span></div>'
            f'<div class="reason">Reason: {escape(str(pipe.get("reason")))}</div><div class="pipeline">{stage_html}</div></section>'
        )
    empty = '<section class="empty">No runtime profile evidence is available.</section>' if not cards else ''
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AFIP Live Execution Pipeline</title><!-- legacy refresh contract: http-equiv="refresh" content="5"; active refresh preserves scroll via JavaScript --><style>
:root{{font-family:Arial,"Noto Sans Thai",sans-serif;color:#172033;background:#eef2f7}}*{{box-sizing:border-box}}html{{scroll-behavior:auto;overflow-y:scroll}}body{{margin:0;padding:14px 14px 240px;min-width:1180px;min-height:calc(100vh + 1px);overflow:visible}}.top{{display:flex;justify-content:space-between;gap:12px;align-items:end;margin-bottom:12px}}h1{{margin:0;font-size:22px}}.top p{{margin:4px 0 0;color:#64748b;font-size:12px}}.policy{{font-size:11px;background:#e8fff3;border:1px solid #9be0bc;padding:8px 10px;border-radius:9px;white-space:nowrap}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:start}}.card{{min-width:0;background:white;border:1px solid #dce4ef;border-radius:12px;box-shadow:0 4px 12px #1720330c;overflow:hidden}}header{{display:flex;justify-content:space-between;gap:6px;padding:11px 12px;border-bottom:1px solid #e8edf4}}h2{{font-size:15px;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}header p{{font-size:9px;color:#64748b;margin:4px 0 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.badge{{font-size:9px;font-weight:800;padding:5px 7px;border-radius:999px;background:#eef2f7;height:max-content;white-space:nowrap}}.summary{{display:grid;grid-template-columns:1fr 1fr;gap:5px 8px;padding:9px 12px;font-size:10px;background:#f8fafc}}.summary span{{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}.reason{{padding:8px 12px;font-size:10px;border-bottom:1px solid #edf1f6;min-height:42px;overflow-wrap:anywhere}}.pipeline{{padding:7px 12px 10px}}.stage{{display:grid;grid-template-columns:9px minmax(0,1fr) auto;gap:7px;align-items:center;padding:6px 0;border-bottom:1px dashed #e3e9f1}}.stage:last-child{{border-bottom:0}}.dot{{width:8px;height:8px;border-radius:50%;background:#94a3b8}}.stage strong{{display:block;font-size:10px;line-height:1.15}}.stage small{{display:block;color:#64748b;font-size:8.5px;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.stage b{{font-size:8.5px;white-space:nowrap}}.pass .dot{{background:#16a34a}}.waiting .dot{{background:#f59e0b}}.blocked .dot,.failed .dot{{background:#dc2626}}.data_unavailable .dot,.not_evaluated .dot{{background:#94a3b8}}.not_evaluated b{{color:#64748b}}.pass b{{color:#15803d}}.waiting b{{color:#b45309}}.blocked b,.failed b{{color:#b91c1c}}.empty{{padding:30px;background:white;border-radius:12px}}@media(max-width:1300px){{body{{min-width:1080px;padding:10px}}.grid{{gap:7px}}.stage strong{{font-size:9px}}.stage b{{font-size:8px}}}}
</style><script>
(function(){{
  const key='afip_pipeline_scroll';
  const save=()=>sessionStorage.setItem(key,String(window.scrollY));
  window.addEventListener('scroll',save,{{passive:true}});
  window.addEventListener('beforeunload',save);
  window.addEventListener('load',()=>{{
    const y=Number(sessionStorage.getItem(key)||0);
    requestAnimationFrame(()=>requestAnimationFrame(()=>window.scrollTo(0,y)));
    setTimeout(()=>window.scrollTo(0,y),120);
  }});
  setTimeout(()=>{{save(); location.reload();}},5000);
}})();
</script></head><body><div class="top"><div><h1>Live Execution Pipeline · P1–P4 Comparison</h1><p>Four-column comparison · runtime evidence only · refresh every 5 seconds · generated {generated}</p></div><div class="policy">Read-only · No authority calculation · No MT5 initialization · No order send</div></div><main class="grid">{''.join(cards)}{empty}</main></body></html>'''


def write_execution_pipeline_dashboard(contract: Mapping[str, Any], output_directory: str | Path = "runtime/dashboard") -> Path:
    path = Path(output_directory) / PIPELINE_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_execution_pipeline_dashboard(contract), encoding="utf-8")
    return path
