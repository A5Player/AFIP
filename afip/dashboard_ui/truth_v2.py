"""AFIP Dashboard V2 passive truth, lineage, and consistency viewer.

This module reads existing AFIP runtime and research artifacts only. It does
not start MT5, research, execution, or mutate any authority/configuration.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping

FILENAME = "afip_dashboard_v2_truth.html"
SCHEMA_VERSION = "afip-dashboard-v2-truth.v2"
MISSING = (None, "", "NOT_RECORDED", "DATA_UNAVAILABLE", "UNKNOWN", "NONE_RECORDED")
ID_FIELDS = (
    "signal_id", "signal_key", "decision_id", "plan_id", "trade_plan_id",
    "request_id", "order_id", "order_ticket", "ticket", "position_ticket",
    "position_id", "deal_ticket", "close_ticket", "exit_id", "trade_case_id",
    "research_case_id", "case_id", "pattern_id", "execution_trace_id",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _read_jsonl(path: Path, limit: int = 10000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()[-limit:]
    except OSError:
        return rows
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, Mapping):
            rows.append(dict(value))
    return rows


def _first(record: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in MISSING:
            return value
    return None


def _numeric(record: Mapping[str, Any], *keys: str) -> float | None:
    value = _first(record, *keys)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_time(value: Any) -> datetime | None:
    if value in MISSING:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _time(record: Mapping[str, Any]) -> Any:
    return _first(record, "timestamp_utc", "updated_at_utc", "created_at_utc", "decision_time", "execution_time", "opened_at_utc", "closed_at_utc", "time", "timestamp")


def _find_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for base in (root / "runtime", root / "data", root / "research"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl"}:
                continue
            rel = str(path.relative_to(root)).replace("\\", "/")
            values: Iterable[Any]
            if path.suffix.lower() == ".jsonl":
                values = _read_jsonl(path)
            else:
                value = _read_json(path)
                values = value if isinstance(value, list) else [value]
            for value in values:
                if isinstance(value, Mapping):
                    row = dict(value)
                    row["_source"] = rel
                    records.append(row)
    return records


def _ids(record: Mapping[str, Any]) -> set[str]:
    out: set[str] = set()
    for key in ID_FIELDS:
        value = record.get(key)
        if value not in MISSING and not isinstance(value, (dict, list)):
            out.add(f"{key}:{value}")
            # Cross-field linking for ticket-like identifiers.
            if "ticket" in key or key in {"order_id", "position_id", "request_id"}:
                out.add(f"ticketish:{value}")
    return out


def _trade_like(record: Mapping[str, Any]) -> bool:
    keys = set(record)
    return bool(keys & set(ID_FIELDS)) or bool(keys & {"decision", "signal", "pattern", "profit", "pnl", "order_status", "mt5_return_code"})


def _components(records: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Connect records using real shared identifiers; never time/proximity guesses."""
    parent = list(range(len(records)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    index: dict[str, int] = {}
    for i, row in enumerate(records):
        for token in _ids(row):
            if token in index:
                union(i, index[token])
            else:
                index[token] = i
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for i, row in enumerate(records):
        groups[find(i)].append(row)
    return list(groups.values())


def _merged(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    # Oldest to newest lets current state supersede prior state.
    ordered = sorted(rows, key=lambda r: _parse_time(_time(r)) or datetime.min.replace(tzinfo=timezone.utc))
    for row in ordered:
        for key, value in row.items():
            if value not in MISSING:
                result[key] = value
    return result


def _truth(value: Any) -> str:
    if value in MISSING:
        return "Unavailable from current producers"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _lineage(rows: list[dict[str, Any]], sequence: int) -> dict[str, Any]:
    m = _merged(rows)
    sources = sorted({str(r.get("_source", "")) for r in rows if r.get("_source")})
    ticket = _first(m, "position_ticket", "ticket", "order_ticket", "deal_ticket", "mt5_ticket")
    return {
        "lineage_id": _first(m, "execution_trace_id", "trade_case_id", "research_case_id", "decision_id", "signal_id") or f"lineage-{sequence}",
        "ticket": ticket,
        "signal": _first(m, "signal_id", "signal", "signal_key"),
        "pattern": _first(m, "pattern_id", "pattern", "pattern_name"),
        "pattern_family": _first(m, "pattern_family", "family"),
        "decision": _first(m, "decision_id", "decision", "decision_action"),
        "plan": _first(m, "plan_id", "trade_plan_id", "strategy", "strategy_id"),
        "order": _first(m, "order_ticket", "order_id", "request_id"),
        "position": _first(m, "position_ticket", "position_id", "ticket"),
        "exit": _first(m, "exit_id", "close_ticket", "deal_ticket", "exit_reason"),
        "research_case": _first(m, "research_case_id", "trade_case_id", "case_id"),
        "market_regime": _first(m, "market_regime", "regime"),
        "strategy": _first(m, "strategy", "strategy_id", "plan_name"),
        "confidence": _first(m, "confidence", "decision_confidence", "research_confidence"),
        "dataset": _first(m, "research_dataset", "dataset_id", "dataset_version"),
        "matching_cases": _first(m, "matching_historical_cases", "historical_sample_size", "sample_size"),
        "historical_success_rate": _first(m, "historical_success_rate", "win_rate"),
        "nearest_similar_trades": _first(m, "nearest_similar_trades", "nearest_cases"),
        "top_similar_trades": _first(m, "top_similar_trades", "similar_trades"),
        "sources": sources,
        "record_count": len(rows),
    }


def _warnings(lineage: Mapping[str, Any]) -> list[dict[str, Any]]:
    stages = ("signal", "decision", "order", "position")
    missing = [stage for stage in stages if lineage.get(stage) in MISSING]
    warnings: list[dict[str, Any]] = []
    if missing:
        warnings.append({
            "lineage_id": lineage.get("lineage_id"), "ticket": lineage.get("ticket"),
            "type": "LINEAGE_GAP", "severity": "WARNING", "missing": missing,
            "explanation": "No matching identifier was found in the current runtime/research producer records. The dashboard did not infer a link.",
            "sources": lineage.get("sources"),
        })
    checks = (
        ("POSITION_WITHOUT_TICKET", lineage.get("position") not in MISSING and lineage.get("ticket") in MISSING, "A position record exists but no ticket identifier was produced."),
        ("TICKET_WITHOUT_ORDER", lineage.get("ticket") not in MISSING and lineage.get("order") in MISSING, "A ticket exists without a matching order identifier."),
        ("ORDER_WITHOUT_DECISION", lineage.get("order") not in MISSING and lineage.get("decision") in MISSING, "An order exists without a matching decision identifier."),
        ("DECISION_WITHOUT_SIGNAL", lineage.get("decision") not in MISSING and lineage.get("signal") in MISSING, "A decision exists without a matching signal identifier."),
        ("RESEARCH_MISMATCH", lineage.get("research_case") in MISSING and lineage.get("ticket") not in MISSING, "The trade has no linked research case in current producer data."),
    )
    for kind, condition, explanation in checks:
        if condition:
            warnings.append({"lineage_id": lineage.get("lineage_id"), "ticket": lineage.get("ticket"), "type": kind, "severity": "WARNING", "missing": None, "explanation": explanation, "sources": lineage.get("sources")})
    return warnings


def _period_analytics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    starts = {
        "today": now.replace(hour=0, minute=0, second=0, microsecond=0),
        "week": (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0),
        "month": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        "year": now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
    }
    values: dict[str, list[float]] = {k: [] for k in starts}
    all_pnl: list[float] = []
    floating: list[float] = []
    holding: list[float] = []
    rr: list[float] = []
    exposure: list[float] = []
    for row in rows:
        pnl = _numeric(row, "realized_profit", "closed_profit", "profit", "pnl")
        dt = _parse_time(_first(row, "closed_at_utc", "exit_time", "timestamp_utc", "updated_at_utc", "time"))
        if pnl is not None:
            all_pnl.append(pnl)
            if dt:
                for name, start in starts.items():
                    if dt >= start:
                        values[name].append(pnl)
        val = _numeric(row, "floating_profit", "unrealized_profit")
        if val is not None:
            floating.append(val)
        val = _numeric(row, "holding_seconds", "duration_seconds")
        if val is not None:
            holding.append(val)
        val = _numeric(row, "rr", "risk_reward", "realized_rr")
        if val is not None:
            rr.append(val)
        val = _numeric(row, "exposure", "notional_exposure", "maximum_exposure")
        if val is not None:
            exposure.append(val)
    wins = [v for v in all_pnl if v > 0]
    losses = [v for v in all_pnl if v < 0]
    return {
        "today_realized_profit": sum(values["today"]) if values["today"] else None,
        "week_realized_profit": sum(values["week"]) if values["week"] else None,
        "month_realized_profit": sum(values["month"]) if values["month"] else None,
        "year_realized_profit": sum(values["year"]) if values["year"] else None,
        "total_realized_profit": sum(all_pnl) if all_pnl else None,
        "floating_profit": sum(floating) if floating else None,
        "maximum_exposure": max(exposure) if exposure else None,
        "average_holding_seconds": mean(holding) if holding else None,
        "average_rr": mean(rr) if rr else None,
        "average_win": mean(wins) if wins else None,
        "average_loss": mean(losses) if losses else None,
        "profit_factor": (sum(wins) / abs(sum(losses))) if losses else ("No recorded losses" if wins else None),
        "deposit": next((_numeric(r, "deposit", "deposits", "total_deposits") for r in reversed(rows) if _numeric(r, "deposit", "deposits", "total_deposits") is not None), None),
        "withdrawal": next((_numeric(r, "withdrawal", "withdrawals", "total_withdrawals") for r in reversed(rows) if _numeric(r, "withdrawal", "withdrawals", "total_withdrawals") is not None), None),
        "reserve": next((_numeric(r, "reserve", "configured_reserve") for r in reversed(rows) if _numeric(r, "reserve", "configured_reserve") is not None), None),
        "capital_allocation": next((_numeric(r, "capital_allocation", "available_allocation", "allocation") for r in reversed(rows) if _numeric(r, "capital_allocation", "available_allocation", "allocation") is not None), None),
    }


def _execution_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if not any(k in row for k in ("execution_time", "latency_ms", "slippage", "retry_count", "mt5_return_code", "broker_response", "execution_result")):
            continue
        out.append({
            "time": _time(row), "ticket": _first(row, "position_ticket", "ticket", "order_ticket"),
            "decision_time": _first(row, "decision_time", "decision_at_utc"),
            "execution_time": _first(row, "execution_time", "executed_at_utc", "timestamp_utc"),
            "latency_ms": _first(row, "latency_ms", "execution_latency_ms", "broker_latency_ms"),
            "slippage": _first(row, "slippage", "slippage_points"),
            "retry_count": _first(row, "retry_count", "retries"),
            "execution_result": _first(row, "execution_result", "order_status", "status"),
            "broker_response": _first(row, "broker_response", "mt5_comment", "comment"),
            "mt5_return_code": _first(row, "mt5_return_code", "retcode", "result_code"),
            "execution_trace": _first(row, "execution_trace_id", "trace_id", "request_id"),
            "source": row.get("_source"),
        })
    out.sort(key=lambda r: str(r.get("time") or ""), reverse=True)
    return out[:500]


def build_truth_snapshot(project_root: str | Path = ".") -> dict[str, Any]:
    root = Path(project_root).resolve()
    records = _find_records(root)
    trade_records = [r for r in records if _trade_like(r)]
    components = _components(trade_records)
    lineages = [_lineage(rows, i + 1) for i, rows in enumerate(components)]
    # Put ticketed and recent lineages first.
    lineages.sort(key=lambda x: (x.get("ticket") in MISSING, str(x.get("ticket") or x.get("lineage_id"))))
    warnings = [w for lineage in lineages for w in _warnings(lineage)]
    timeline: list[dict[str, Any]] = []
    for lineage, rows in zip([_lineage(rows, i + 1) for i, rows in enumerate(components)], components):
        for row in rows:
            timeline.append({
                "time": _time(row), "lineage_id": lineage["lineage_id"], "ticket": lineage.get("ticket"),
                "event": _first(row, "event", "event_type", "status", "order_status", "decision", "reason"),
                "stage": next((s for s in ("signal", "decision", "order", "position", "management", "exit", "research", "archive") if s in str(row.get("_source", "")).lower() or s in str(_first(row, "event", "event_type") or "").lower()), None),
                "source": row.get("_source"),
            })
    timeline.sort(key=lambda r: str(r.get("time") or ""), reverse=True)

    research_summary: dict[str, Any] = {}
    research_fields = ("market_regime", "pattern", "pattern_family", "strategy", "confidence", "historical_sample_size", "win_rate", "loss_rate", "profit_factor", "expectancy", "maximum_drawdown", "recovery", "research_coverage", "database_status", "research_version")
    for row in records:
        for key in research_fields:
            if research_summary.get(key) in MISSING and row.get(key) not in MISSING:
                research_summary[key] = row.get(key)
                research_summary[f"{key}_source"] = row.get("_source")

    return {
        "schema_version": SCHEMA_VERSION, "generated_at": _utc_now(), "project_root": str(root),
        "source_file_count": len({r.get("_source") for r in records}), "record_count": len(records),
        "lineages": lineages[:1000], "timeline": timeline[:1000], "warnings": warnings[:1000],
        "analytics": _period_analytics(records), "execution": _execution_rows(records), "research": research_summary,
        "consistency": {
            "status": "PASS" if not warnings else "REVIEW_REQUIRED",
            "warning_count": len(warnings),
            "lineage_count": len(lineages),
            "complete_lineage_count": sum(1 for x in lineages if all(x.get(k) not in MISSING for k in ("signal", "decision", "order", "position"))),
        },
        "execution_authority_changed": False, "read_only": True,
    }


def _table(rows: list[Mapping[str, Any]], columns: tuple[str, ...]) -> str:
    if not rows:
        return '<p class="empty">No matching records were produced.</p>'
    head = "".join(f"<th>{escape(c.replace('_', ' ').title())}</th>" for c in columns)
    body = "".join("<tr>" + "".join(f"<td>{escape(_truth(row.get(c)))}</td>" for c in columns) + "</tr>" for row in rows)
    return f"<div class='scroll'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def render_truth_dashboard(project_root: str | Path = ".") -> str:
    snap = build_truth_snapshot(project_root)
    cards = "".join(f"<article><h3>{escape(k.replace('_',' ').title())}</h3><strong>{escape(_truth(v))}</strong></article>" for k, v in snap["analytics"].items())
    consistency_cards = "".join(f"<article><h3>{escape(k.replace('_',' ').title())}</h3><strong>{escape(_truth(v))}</strong></article>" for k, v in snap["consistency"].items())
    research_rows = [{"metric": k, "value": v, "source": snap["research"].get(f"{k}_source")} for k, v in snap["research"].items() if not k.endswith("_source")]
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="10"><title>AFIP Dashboard V2 Truth</title><style>
:root{{font-family:Arial,'Noto Sans Thai',sans-serif;color:#172033;background:#eef2f7}}*{{box-sizing:border-box}}body{{margin:0}}main{{max-width:1800px;margin:auto;padding:18px}}header,section,article{{background:#fff;border:1px solid #d8e0ea;border-radius:12px}}header,section{{padding:16px;margin-bottom:14px}}h1,h2,h3{{margin-top:0}}.nav a{{display:inline-block;margin:0 6px 6px 0;padding:8px 10px;background:#16243b;color:#fff;border-radius:8px;text-decoration:none}}.cards{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}}.cards article{{padding:12px;overflow-wrap:anywhere}}.scroll{{overflow:auto}}table{{width:100%;border-collapse:collapse;font-size:12px}}th,td{{padding:8px;border-bottom:1px solid #e8edf3;text-align:left;vertical-align:top;max-width:360px;overflow-wrap:anywhere}}th{{background:#f6f8fb;position:sticky;top:0}}.safe{{color:#146c43;font-weight:700}}.warn{{color:#9b5b00}}.empty{{color:#64748b}}@media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr)}}}}@media(max-width:600px){{.cards{{grid-template-columns:1fr}}}}
</style></head><body><main><header><div class="nav"><a href="afip_dashboard.html">Home</a><a href="afip_control_center.html">Control Center</a><a href="afip_research_data_dashboard.html">Research</a></div><h1>AFIP Dashboard V2 — Truth Lineage & Research Integration</h1><p class="safe">READ ONLY · Real producer records only · No inferred links · Execution authority unchanged</p><p>Generated {escape(str(snap['generated_at']))} · {snap['source_file_count']} source files · {snap['record_count']} records</p></header>
<section><h2>Consistency Summary</h2><div class="cards">{consistency_cards}</div></section>
<section><h2>Performance Analytics</h2><div class="cards">{cards}</div><p class="empty">Unavailable means no real producer field was found. Values are never fabricated.</p></section>
<section><h2>Trade Plan Lineage</h2>{_table(snap['lineages'], ('lineage_id','ticket','signal','pattern','pattern_family','decision','plan','order','position','exit','research_case','market_regime','strategy','confidence','dataset','matching_cases','historical_success_rate','record_count','sources'))}</section>
<section><h2>Execution Analytics</h2>{_table(snap['execution'], ('time','ticket','decision_time','execution_time','latency_ms','slippage','retry_count','execution_result','broker_response','mt5_return_code','execution_trace','source'))}</section>
<section><h2>Research Integration</h2>{_table(research_rows, ('metric','value','source'))}</section>
<section><h2>Consistency Warnings with Explanation</h2>{_table(snap['warnings'], ('lineage_id','ticket','type','severity','missing','explanation','sources'))}</section>
<section><h2>Dashboard Timeline</h2>{_table(snap['timeline'], ('time','lineage_id','ticket','stage','event','source'))}</section>
</main></body></html>'''


def write_truth_dashboard(output_directory: str | Path = "runtime/dashboard", project_root: str | Path = ".") -> Path:
    output = Path(output_directory) / FILENAME
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(render_truth_dashboard(project_root), encoding="utf-8")
    temporary.replace(output)
    snapshot_path = Path(project_root) / "runtime" / "dashboard" / "dashboard_v2_truth.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    temp_json = snapshot_path.with_suffix(".json.tmp")
    temp_json.write_text(json.dumps(build_truth_snapshot(project_root), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    temp_json.replace(snapshot_path)
    return output
