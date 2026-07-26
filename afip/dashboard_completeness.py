"""Read-only AFIP dashboard data-completeness assessment and renderer."""
from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Mapping

REQUIRED_PROFILE_FIELDS = (
    "account", "server", "currency", "balance", "equity", "free_margin",
    "positions_total", "orders_total", "bid", "ask", "spread_points",
    "connection_status", "checked_at_utc",
)
OPTIONAL_EXECUTION_FIELDS = (
    "runtime_state", "decision_action", "decision_confidence", "market_regime",
    "demo_gateway_status", "demo_gateway_reason", "order_status", "sent_units",
)


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _first(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if _present(row.get(key)):
            return row.get(key)
    return None


def assess_dashboard_completeness(contract: Mapping[str, Any]) -> dict[str, Any]:
    rows = contract.get("profiles") if isinstance(contract.get("profiles"), list) else []
    profiles: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        available: list[str] = []
        missing: list[str] = []
        aliases = {
            "account": ("account", "login", "account_login"),
            "balance": ("balance", "account_balance"),
            "equity": ("equity", "account_equity"),
            "free_margin": ("free_margin", "account_free_margin", "margin_free"),
            "connection_status": ("connection_status", "mt5_connection"),
        }
        for field in REQUIRED_PROFILE_FIELDS:
            value = _first(row, *aliases.get(field, (field,)))
            (available if _present(value) else missing).append(field)
        execution_available = [f for f in OPTIONAL_EXECUTION_FIELDS if _present(row.get(f))]
        execution_missing = [f for f in OPTIONAL_EXECUTION_FIELDS if not _present(row.get(f))]
        truth = row.get("runtime_truth") if isinstance(row.get("runtime_truth"), Mapping) else {}
        profiles.append({
            "profile_id": str(row.get("profile_id", "UNKNOWN")),
            "required_available": available,
            "required_missing": missing,
            "required_coverage_percent": round(100.0 * len(available) / len(REQUIRED_PROFILE_FIELDS), 1),
            "execution_available": execution_available,
            "execution_missing": execution_missing,
            "mt5_current": truth.get("mt5_current", _first(row, "connection_status", "mt5_connection")),
            "runtime_current": truth.get("runtime_current", row.get("runtime_state")),
            "gateway_current": truth.get("gateway_current", row.get("demo_gateway_status")),
            "data_status": row.get("data_status", "DATA_UNAVAILABLE"),
        })
    research = contract.get("research") if isinstance(contract.get("research"), Mapping) else {}
    research_keys = [
        "status", "accepted_events", "scanned_profiles", "trade_cases_written",
        "historical_data", "timeframe_data_quality", "replay_timeframe_evidence",
    ]
    research_available = [k for k in research_keys if _present(research.get(k))]
    ranking_present = any(_present(research.get(k)) for k in ("rankings", "top_patterns", "top_100"))
    return {
        "status": "READY" if profiles and all(not p["required_missing"] for p in profiles) else "REVIEW",
        "profiles": profiles,
        "research": {
            "available_fields": research_available,
            "missing_fields": [k for k in research_keys if k not in research_available],
            "ranking_status": "READY" if ranking_present else "NOT_GENERATED",
            "data_status": "AVAILABLE" if research_available else "DATA_UNAVAILABLE",
        },
        "policy": {
            "read_only": True,
            "missing_values_are_not_invented": True,
            "not_generated_is_distinct_from_data_unavailable": True,
        },
    }


def attach_dashboard_completeness(contract: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(contract)
    payload["dashboard_completeness"] = assess_dashboard_completeness(payload)
    return payload


def write_dashboard_completeness(contract: Mapping[str, Any], output_directory: str | Path) -> Path:
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    assessment = assess_dashboard_completeness(contract)
    cards = []
    for p in assessment["profiles"]:
        missing = ", ".join(p["required_missing"]) or "NONE"
        exec_missing = ", ".join(p["execution_missing"]) or "NONE"
        cards.append(f"""
        <article><h2>{escape(p['profile_id'])}</h2>
        <p><b>Required coverage:</b> {p['required_coverage_percent']}%</p>
        <p><b>MT5 / Runtime / Gateway:</b> {escape(str(p['mt5_current']))} / {escape(str(p['runtime_current']))} / {escape(str(p['gateway_current']))}</p>
        <p><b>Data status:</b> {escape(str(p['data_status']))}</p>
        <p><b>Required missing:</b> {escape(missing)}</p>
        <p><b>Execution evidence missing:</b> {escape(exec_missing)}</p></article>""")
    r = assessment["research"]
    html = f"""<!doctype html><html><head><meta charset='utf-8'><meta http-equiv='refresh' content='5'>
<title>AFIP Dashboard Completeness</title><style>
body{{font-family:Arial,sans-serif;background:#eef2f5;margin:0;padding:16px;color:#17202a}}header,article{{background:white;border:1px solid #d9e0e6;border-radius:12px;padding:14px;margin-bottom:12px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}}a{{color:#1557a0}}</style></head><body>
<header><a href='afip_dashboard.html'>← Dashboard Home</a><h1>AFIP Dashboard Data Completeness</h1>
<p>Shows exactly which real runtime fields are available, missing, stale, or not generated. No values are invented.</p></header>
<div class='grid'>{''.join(cards)}</div>
<article><h2>Research</h2><p><b>Data status:</b> {escape(r['data_status'])}</p>
<p><b>Ranking status:</b> {escape(r['ranking_status'])}</p>
<p><b>Available:</b> {escape(', '.join(r['available_fields']) or 'NONE')}</p>
<p><b>Missing:</b> {escape(', '.join(r['missing_fields']) or 'NONE')}</p></article>
</body></html>"""
    path = output / "afip_dashboard_completeness.html"
    path.write_text(html, encoding="utf-8")
    return path
