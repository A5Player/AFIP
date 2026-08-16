"""Build the fail-closed A38 research-readiness view without execution authority."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
from typing import Any


REPORTS = {
    "A32": "runtime/research/a32_real_backtest/a32_real_backtest_campaign.json",
    "A33": "runtime/research/a33_multi_objective_ranking/a33_multi_objective_ranking.json",
    "A35": "runtime/research/a35_atr_buffer/a35_atr_buffer_campaign.json",
    "A36": "runtime/research/a36_cross_market_capital/a36_cross_market_capital_report.json",
    "A37": "runtime/research/a37_continuous_research_status.json",
}
OUTPUT_DIRECTORY = "runtime/research/a38_research_readiness"


def _load(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _integer(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _eligible_a33(report: dict[str, Any] | None) -> list[dict[str, Any]]:
    rankings = report.get("rankings", {}) if report else {}
    balanced = rankings.get("balanced", ()) if isinstance(rankings, dict) else ()
    return [dict(row) for row in balanced
            if isinstance(row, dict) and row.get("eligibility") in {"ELIGIBLE", "ELIGIBLE_RESEARCH"}]


def _eligible_a35(report: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = report.get("rows", ()) if report else ()
    return [dict(row) for row in rows
            if isinstance(row, dict) and row.get("eligibility") == "ELIGIBLE_RESEARCH"]


def _candidate(row: dict[str, Any], family: str, fallback_rank: int,
               point_size: float) -> dict[str, Any]:
    sl_points = row.get("sl_points", row.get("average_sl_points"))
    tp_points = row.get("tp_points", row.get("average_tp_points"))
    def price_distance(value: Any) -> float | None:
        try:
            return round(float(value) * point_size, 6)
        except (TypeError, ValueError):
            return None
    return {
        "candidate_family": family,
        "rank": row.get("rank", fallback_rank),
        "pattern": row.get("pattern", "UNKNOWN"),
        "timeframe": row.get("timeframe", "UNKNOWN"),
        "market_regime": row.get("market_regime", "DATA_UNAVAILABLE"),
        "direction": row.get("direction", "UNKNOWN"),
        "entry_condition": row.get("entry_condition", row.get("pattern", "DATA_UNAVAILABLE")),
        "samples": _integer(row.get("samples")),
        "win_rate_pct": row.get("win_rate_pct"),
        "expectancy_r": row.get("expectancy_r"),
        "profit_factor": row.get("profit_factor"),
        "max_drawdown_r": row.get("max_drawdown_r"),
        "sl_distance_points": sl_points,
        "tp_distance_points": tp_points,
        "sl_price_distance": price_distance(sl_points),
        "tp_price_distance": price_distance(tp_points),
        "planned_rr": row.get("planned_rr", row.get("average_planned_rr")),
        "atr_multiplier": row.get("sl_atr_multiplier", "NOT_APPLICABLE"),
        "buffer_points": row.get("sl_buffer_points", "NOT_APPLICABLE"),
        "maximum_holding_bars": row.get("max_holding_bars", "DATA_UNAVAILABLE"),
        "average_holding_bars": row.get("average_holding_bars", "DATA_UNAVAILABLE"),
        "walk_forward_passes": _integer(row.get("walk_forward_passes")),
        "walk_forward_windows": _integer(row.get("walk_forward_windows", 4)),
        "research_eligibility": row.get("eligibility", "ELIGIBLE_RESEARCH"),
        "demo_authorization_status": "PROHIBITED_SEPARATE_APPROVAL_REQUIRED",
        "live_authorization_status": "PROHIBITED",
    }


def build_report(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    loaded = {name: _load(root / relative) for name, relative in REPORTS.items()}
    missing = [relative for name, relative in REPORTS.items() if loaded[name] is None]
    a32_rows = len(loaded["A32"].get("rows", ())) if loaded["A32"] else 0
    a33_rows = _eligible_a33(loaded["A33"])
    a35_rows = _eligible_a35(loaded["A35"])
    a36_count = _integer(loaded["A36"].get("candidate_count")) if loaded["A36"] else 0
    try:
        point_size = float(loaded["A35"].get("point_size", 0.01)) if loaded["A35"] else 0.01
    except (TypeError, ValueError):
        point_size = 0.01
    if point_size <= 0:
        point_size = 0.01

    blockers: list[str] = []
    if missing:
        blockers.append("REQUIRED_RESEARCH_REPORTS_MISSING")
    if not a33_rows:
        blockers.append("A33_NO_ELIGIBLE_BALANCED_ROWS")
    if not a35_rows:
        blockers.append("A35_NO_ELIGIBLE_ATR_BUFFER_ROWS")
    if loaded["A36"] is None:
        blockers.append("A36_CROSS_MARKET_REPORT_UNAVAILABLE")
    if loaded["A37"] is not None and loaded["A37"].get("status") != "READY":
        blockers.append("A37_CONTINUOUS_RESEARCH_NOT_READY")

    ready = not blockers
    source_rows = a33_rows if a33_rows else a35_rows
    candidates = [_candidate(row, "A33_BALANCED" if a33_rows else "A35_ATR_BUFFER", index, point_size)
                  for index, row in enumerate(source_rows[:100], 1)]
    return {
        "schema": "afip.a38.research_readiness.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "READY_FOR_MANUAL_DEMO_REVIEW" if ready else "BLOCKED_RESEARCH_EVIDENCE_INCOMPLETE",
        "research_stage": "RESEARCH" if not ready else "MANUAL_DEMO_REVIEW_ELIGIBLE",
        "instrument": "GOLD#",
        "point_size": point_size,
        "point_definition": f"1 point = {point_size:g} GOLD# price distance",
        "price_display_notice": "SL/TP values are distances from entry, never absolute GOLD# market prices.",
        "summary": {
            "a32_rows": a32_rows,
            "a33_eligible_balanced_rows": len(a33_rows),
            "a35_eligible_atr_buffer_rows": len(a35_rows),
            "a36_cross_market_candidate_count": a36_count,
            "missing_report_count": len(missing),
        },
        "missing_reports": missing,
        "blocking_reasons": blockers,
        "next_required_action": ("MANUAL_REVIEW_AND_SEPARATE_BOUNDED_DEMO_APPROVAL" if ready
                                 else "CONTINUE_RESEARCH_UNTIL_ALL_GATES_PASS"),
        "candidates": candidates,
        "profile_strategy_selection": "NOT_DECIDED",
        "automatic_profile_assignment": False,
        "demo_order_authorized": False,
        "live_order_authorized": False,
        "execution_authority": "NONE",
        "orders_sent": False,
        "safety_notice": "Research eligibility never grants Demo or Live execution authority.",
    }


def _value(value: Any, digits: int = 2) -> str:
    if value is None or value == "DATA_UNAVAILABLE":
        return "DATA_UNAVAILABLE"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def render_html(report: dict[str, Any]) -> str:
    summary = report["summary"]
    metrics = "".join(
        f'<div class="metric"><small>{escape(label)}</small><strong>{escape(str(value))}</strong></div>'
        for label, value in (
            ("A32 rows", summary["a32_rows"]),
            ("A33 eligible", summary["a33_eligible_balanced_rows"]),
            ("A35 ATR eligible", summary["a35_eligible_atr_buffer_rows"]),
            ("A36 candidates", summary["a36_cross_market_candidate_count"]),
            ("Missing reports", summary["missing_report_count"]),
        )
    )
    blockers = "".join(f"<li>{escape(str(item))}</li>" for item in report["blocking_reasons"])
    if not blockers:
        blockers = "<li>NONE — research gates passed for manual review only.</li>"
    cards = []
    for row in report["candidates"]:
        cards.append(f'''<article class="candidate">
<h3>🏆 {escape(str(row["candidate_family"]))} · Rank {escape(str(row["rank"]))}</h3>
<p>📈 <b>{escape(str(row["pattern"]))}</b> · {escape(str(row["timeframe"]))} · {escape(str(row["direction"]))}</p>
<p>🧪 Samples {_value(row["samples"])} · Win {_value(row["win_rate_pct"])}% · Expectancy {_value(row["expectancy_r"], 3)}R · PF {_value(row["profit_factor"])}</p>
<p>🛡️ Drawdown {_value(row["max_drawdown_r"])}R · WF {row["walk_forward_passes"]}/{row["walk_forward_windows"]}</p>
<p>📏 SL distance {_value(row["sl_distance_points"])} points = {_value(row["sl_price_distance"], 4)} price · TP distance {_value(row["tp_distance_points"])} points = {_value(row["tp_price_distance"], 4)} price</p>
<p class="safe">✅ Research: {escape(str(row["research_eligibility"]))}<br>⛔ Demo: {escape(str(row["demo_authorization_status"]))} · Live: {escape(str(row["live_authorization_status"]))}</p>
</article>''')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>A38 Research Readiness</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#eef3f8;color:#14243a;font:15px system-ui}}main{{max-width:1280px;margin:auto;padding:24px}}header,.panel,.candidate{{background:#fff;border:1px solid #d7e0e9;border-radius:14px;padding:18px;margin:14px 0;box-shadow:0 4px 14px #1231}}.metrics,.candidates{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}.metric{{background:#f3f7fb;border-radius:10px;padding:12px}}.metric strong{{display:block;font-size:24px}}.candidate{{margin:0;border-left:6px solid #2878c8}}.candidate p{{margin:7px 0;line-height:1.35}}.safe{{background:#fff3d6;padding:10px;border-radius:8px}}.blocked{{color:#a12a2a}}.ready{{color:#147449}}@media(max-width:700px){{main{{padding:12px}}}}</style></head><body><main>
<header><h1>🧭 A38 Research Readiness &amp; Demo Eligibility</h1><h2 class="{'ready' if report['status'].startswith('READY') else 'blocked'}">{escape(report['status'])}</h2><p>{escape(report['safety_notice'])}</p><p><b>GOLD# unit:</b> {escape(report['point_definition'])}. SL/TP below are distances from entry—not the current GOLD# price.</p></header>
<section class="panel"><h2>📊 Evidence summary</h2><div class="metrics">{metrics}</div><h3>🚧 Blocking reasons</h3><ul>{blockers}</ul><p><b>Next action:</b> {escape(report['next_required_action'])}</p><p>Profile strategy: NOT_DECIDED · Demo authorized: false · Live authorized: false · Execution authority: NONE</p></section>
<section><h2>🔎 Eligible research candidates</h2><div class="candidates">{''.join(cards) or '<article class="candidate"><p>No candidate is eligible for manual review.</p></article>'}</div></section>
</main></body></html>'''


def write_outputs(report: dict[str, Any], project_root: str | Path) -> tuple[Path, Path]:
    directory = Path(project_root).resolve() / OUTPUT_DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "a38_research_readiness.json"
    html_path = directory / "a38_research_readiness.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    return json_path, html_path


def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP A38 fail-closed research readiness gate")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    report = build_report(args.project_root)
    json_path, html_path = write_outputs(report, args.project_root)
    print(json.dumps({"status": report["status"], "json": str(json_path), "html": str(html_path),
                      "demo_order_authorized": False, "live_order_authorized": False,
                      "execution_authority": "NONE"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
