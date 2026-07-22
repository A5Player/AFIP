"""Professional read-only dashboard for AFIP data loading and research operations."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from afip.runtime_observatory import RuntimeProgressAuthority

FILENAME = "afip_research_operations_dashboard.html"
TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError, UnicodeError):
        return {}


def _number(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _first(mapping: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return default


def _status_class(value: Any) -> str:
    text = str(value or "UNKNOWN").upper()
    if text in {"READY", "RUNNING", "COMPLETE", "COMPLETED", "PASS", "ELIGIBLE"}:
        return "ok"
    if text in {"FAILED", "FAIL", "BLOCKED", "ERROR", "STALE"}:
        return "bad"
    return "wait"


def _progress(processed: int, total: int) -> tuple[float, str]:
    percent = min(100.0, max(0.0, processed * 100.0 / total)) if total > 0 else 0.0
    return percent, f"{processed:,} / {total:,}"


def _discover_status(root: Path) -> dict[str, Any]:
    candidates = (
        root / "runtime" / "research" / "runtime_observatory_status.json",
        root / "runtime" / "research" / "automatic_research_status.json",
        root / "runtime" / "research" / "continuous_research_status.json",
        root / "runtime" / "research" / "unified_research_status.json",
    )
    merged: dict[str, Any] = {}
    for path in candidates:
        value = _load_json(path)
        if value:
            merged.update(value)
            merged.setdefault("status_source", str(path.relative_to(root)))
    observatory = RuntimeProgressAuthority(root).classified()
    if observatory and observatory.get("reason") != "runtime_progress_not_recorded":
        merged.update(observatory)
        merged["status_source"] = "runtime/research/runtime_observatory_status.json"
    return merged


def _timeframe_records(status: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {tf: {} for tf in TIMEFRAMES}
    for key in ("timeframes", "timeframe_status", "timeframe_progress", "coverage_by_timeframe", "replay_by_timeframe"):
        value = status.get(key)
        if isinstance(value, dict):
            for tf in TIMEFRAMES:
                item = value.get(tf) or value.get(tf.lower())
                if isinstance(item, dict):
                    result[tf].update(item)
    return result


def _recent_runtime_files(root: Path, limit: int = 12) -> list[tuple[str, int, str]]:
    """Read recent activity without recursively scanning the whole data lake."""
    candidates = (
        root / "runtime" / "final_integration_status.json",
        root / "runtime" / "research" / "research_engine_status.json",
        root / "runtime" / "research" / "runtime_observatory_status.json",
        root / "runtime" / "research" / "automatic_research_status.json",
        root / "runtime" / "research" / "research_live_status.json",
        root / "runtime" / "research" / "research_file_index.json",
        root / "runtime" / "control" / "final_integration" / "dashboard_runtime_status.json",
        root / "runtime" / "logs" / "afip_research_runtime.log",
        root / "runtime" / "logs" / "afip_dashboard_runtime.log",
    )
    values: list[tuple[float, str, int, str]] = []
    for path in candidates:
        try:
            if not path.is_file():
                continue
            stat = path.stat()
            stamp = datetime.fromtimestamp(stat.st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            values.append((stat.st_mtime, str(path.relative_to(root)), stat.st_size, stamp))
        except OSError:
            continue
    values.sort(reverse=True)
    return [(name, size, stamp) for _, name, size, stamp in values[:limit]]


def render_research_operations(root: str | Path = ".") -> str:
    root_path = Path(root).resolve()
    status = _discover_status(root_path)
    tf_rows = _timeframe_records(status)
    current_tf = str(_first(status, "current_timeframe", "active_timeframe", default="NOT_RECORDED"))
    stage = str(_first(status, "stage", "pipeline_stage", default="WAITING"))
    overall = str(_first(status, "status", default="WAITING"))
    reason = str(_first(status, "reason", default="No active research status has been recorded."))
    updated = str(_first(status, "heartbeat_utc", "updated_at_utc", "last_heartbeat_utc", default="NOT_RECORDED"))

    mt5_bars = _number(_first(status, "mt5_bars_collected", "bars_collected"))
    replay_processed = _number(_first(status, "replay_processed", "replay_bars_processed", "processed_bars"))
    replay_total = _number(_first(status, "replay_total", "current_timeframe_available_bars", "maximum_replay_bars", "available_bars"))
    appended = _number(_first(status, "historical_lake_appended", "lake_appended"))
    duplicates = _number(_first(status, "historical_lake_duplicates", "lake_duplicates"))
    gaps = _number(_first(status, "gap_ranges_detected", "gaps_detected"))
    missing = _number(_first(status, "missing_bars_detected", "missing_bars"))
    candidates = _number(_first(status, "replay_candidates", "replay_candidates_generated", "research_candidates"))
    rankings = _number(_first(status, "ranking_records", "rankings_generated"))
    authority_percent = _first(
        status,
        "replay_percent",
        default=None,
    )

    if authority_percent is not None:
        try:
            pct = float(authority_percent)
        except (TypeError, ValueError):
            pct, _ = _progress(
                replay_processed,
                replay_total,
            )
    else:
        pct, _ = _progress(
            replay_processed,
            replay_total,
        )

    _, progress_label = _progress(
        replay_processed,
        replay_total,
    )

    speed = _first(status, "replay_speed_bars_per_second", default=0)
    eta = _first(status, "eta_seconds", default=None)
    candle = str(_first(status, "current_replay_timestamp_utc", "last_processed_candle_utc", default="NOT_RECORDED"))
    cards = [
        ("📥", "MT5 Closed Bars", f"{mt5_bars:,}", "Collected in current/latest cycle"),
        ("🗄️", "Lake Appended", f"{appended:,}", f"Duplicates protected: {duplicates:,}"),
        ("⏯️", "Replay Processed", f"{replay_processed:,}", progress_label),
        ("🧪", "Research Candidates", f"{candidates:,}", "Classified candidates"),
        ("🏆", "Ranking Records", f"{rankings:,}", "Generated ranking evidence"),
        ("⚠️", "Data Gaps", f"{gaps:,}", f"Missing bars: {missing:,}"),
        ("⚡", "Replay Speed", f"{speed} bars/s", f"ETA: {eta if eta is not None else 'CALCULATING'} s"),
        ("🕯️", "Current Candle", candle, "Last processed replay candle"),
    ]
    card_html = "".join(
        f'<article class="metric-card"><div class="metric-icon">{icon}</div><div><div class="metric-label">{escape(label)}</div><div class="metric-value">{escape(value)}</div><div class="metric-note">{escape(note)}</div></div></article>'
        for icon, label, value, note in cards
    )

    rows = []
    for tf in TIMEFRAMES:
        item = tf_rows[tf]
        available = _number(_first(item, "available", "available_bars", "bars"))
        processed = _number(_first(item, "processed", "processed_bars", "replay_processed"))
        covered = _number(_first(item, "covered", "covered_bars", default=processed))
        tf_gaps = _number(_first(item, "gaps", "gap_count"))
        tf_missing = _number(_first(item, "missing", "missing_bars"))
        tf_status = str(_first(item, "status", "replay_status", default="WAITING"))
        tf_pct, _ = _progress(processed, available)
        rows.append(
            f'<tr><td><b>{tf}</b>{" <span class=\"active-dot\">ACTIVE</span>" if tf == current_tf else ""}</td>'
            f'<td>{available:,}</td><td>{processed:,}</td><td>{covered:,}</td><td>{tf_gaps:,} / {tf_missing:,}</td>'
            f'<td><div class="mini-progress"><span style="width:{tf_pct:.1f}%"></span></div><small>{tf_pct:.1f}%</small></td>'
            f'<td><span class="badge {_status_class(tf_status)}">{escape(tf_status)}</span></td></tr>'
        )

    recent = _recent_runtime_files(root_path)
    recent_html = "".join(
        f'<tr><td>{escape(name)}</td><td>{size:,}</td><td>{escape(stamp)}</td></tr>' for name, size, stamp in recent
    ) or '<tr><td colspan="3">No runtime files found.</td></tr>'

    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="5"><title>AFIP Data Loading & Research Operations</title><style>
:root{{--bg:#eef3f8;--panel:#fff;--ink:#17233a;--muted:#65758b;--line:#dbe4ef;--nav:#13213b;--blue:#2878d8;--green:#167b52;--amber:#aa6b00;--red:#b33a3a}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:Arial,"Noto Sans Thai",sans-serif;font-size:13px}}.page{{max-width:1600px;margin:auto;padding:18px}}header{{background:linear-gradient(135deg,#13213b,#1f3f6d);color:white;border-radius:14px;padding:12px 16px;box-shadow:0 8px 24px #14233b22}}.toolbar{{display:flex;align-items:center;gap:9px;flex-wrap:wrap}}.toolbar a,.toolbar button{{border:1px solid #ffffff36;background:#ffffff12;color:#fff;padding:8px 11px;border-radius:8px;text-decoration:none;cursor:pointer}}h1{{font-size:19px;margin:10px 0 4px}}h2{{font-size:17px;margin:0 0 12px}}.sub{{color:#cfddf3;margin:0}}.status-row{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:16px}}.status-box{{background:#ffffff12;border:1px solid #ffffff24;border-radius:10px;padding:10px 12px}}.status-box small{{display:block;color:#bfd0e8;margin-bottom:5px}}.status-box strong{{font-size:14px}}.badge{{display:inline-block;padding:4px 8px;border-radius:999px;font-size:10px;font-weight:800}}.badge.ok{{background:#dff5eb;color:var(--green)}}.badge.wait{{background:#fff1d6;color:var(--amber)}}.badge.bad{{background:#ffe4e4;color:var(--red)}}.metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:16px 0}}.metric-card{{display:flex;gap:11px;align-items:flex-start;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;box-shadow:0 3px 10px #17233a0b;min-width:0}}.metric-icon{{font-size:18px}}.metric-label{{color:var(--muted);font-size:11px;font-weight:700}}.metric-value{{font-size:18px;font-weight:800;margin:3px 0}}.metric-note{{color:var(--muted);font-size:10px}}.panel{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:15px;margin-top:14px;box-shadow:0 3px 10px #17233a0b}}.panel-head{{display:flex;align-items:center;justify-content:space-between;gap:10px}}.overall-progress{{height:12px;background:#e7edf5;border-radius:99px;overflow:hidden;margin-top:10px}}.overall-progress span,.mini-progress span{{display:block;height:100%;background:linear-gradient(90deg,#2878d8,#42a0ff);border-radius:99px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px 10px;border-bottom:1px solid #e6edf5;text-align:left;vertical-align:middle}}th{{font-size:10px;color:#53657b;text-transform:uppercase;letter-spacing:.04em;background:#f7f9fc}}td{{font-size:12px}}.mini-progress{{display:inline-block;width:110px;height:7px;background:#e5ebf3;border-radius:99px;overflow:hidden;margin-right:7px}}.active-dot{{display:inline-block;margin-left:6px;padding:2px 5px;border-radius:5px;background:#dbeafe;color:#1d65b6;font-size:8px}}.reason{{margin-top:10px;padding:10px 12px;background:#f6f9fd;border-left:4px solid var(--blue);color:#40516a;border-radius:6px}}.foot{{color:var(--muted);font-size:10px;margin:13px 2px}}@media(max-width:1200px){{.metrics{{grid-template-columns:repeat(3,1fr)}}.status-row{{grid-template-columns:repeat(2,1fr)}}}}@media(max-width:700px){{.metrics,.status-row{{grid-template-columns:1fr}}.page{{padding:9px}}}}
</style></head><body><div class="page"><header><div class="toolbar"><a href="afip_profiles_dashboard.html">📊 Operations</a><a href="afip_intelligence_engine_dashboard.html">🧠 Intelligence</a><a href="afip_research_data_dashboard.html">🔬 Research & Ranking</a><button onclick="location.reload()">↻ Refresh</button></div><h1>📡 AFIP Dashboard 4 · Data Loading & Research Operations</h1><p class="sub">Live read-only evidence for MT5 history, Data Lake, replay, research and ranking.</p><div class="status-row"><div class="status-box"><small>Runtime Status</small><strong><span class="badge {_status_class(overall)}">{escape(overall)}</span></strong></div><div class="status-box"><small>Current Stage</small><strong>{escape(stage)}</strong></div><div class="status-box"><small>Current Timeframe</small><strong>{escape(current_tf)}</strong></div><div class="status-box"><small>Last Heartbeat</small><strong>{escape(updated)}</strong></div></div><div class="reason"><b>Current activity:</b> {escape(reason)}</div></header><section class="metrics">{card_html}</section><section class="panel"><div class="panel-head"><h2>⏳ Overall Replay Progress</h2><strong>{pct:.1f}%</strong></div><div class="overall-progress"><span style="width:{pct:.1f}%"></span></div><p class="foot">{escape(progress_label)} · Dashboard is read-only and has no execution authority.</p></section><section class="panel"><div class="panel-head"><h2>🕒 M1–D1 Timeframe Pipeline</h2><span class="badge {_status_class(overall)}">AUTO REFRESH 5S</span></div><div style="overflow:auto"><table><thead><tr><th>Timeframe</th><th>Available</th><th>Processed</th><th>Covered</th><th>Gaps / Missing</th><th>Progress</th><th>Status</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section><section class="panel"><h2>🧾 Recent Runtime Activity</h2><div style="overflow:auto"><table><thead><tr><th>Runtime file</th><th>Size</th><th>Last written</th></tr></thead><tbody>{recent_html}</tbody></table></div></section><p class="foot">Generated {escape(generated)} · Source: {escape(str(status.get('status_source','runtime/research/automatic_research_status.json')))} · Live execution authority: DISABLED · execution_authority=false · order_send_called=false</p></div></body></html>'''


def write_research_operations(output_directory: str | Path = "runtime/dashboard", project_root: str | Path = ".") -> Path:
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / FILENAME
    path.write_text(render_research_operations(project_root), encoding="utf-8")
    return path
