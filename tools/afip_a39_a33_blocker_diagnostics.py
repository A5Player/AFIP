"""Explain A33 eligibility blockers without changing research policy or authority."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
from typing import Any


SOURCE = "runtime/research/a33_multi_objective_ranking/a33_multi_objective_ranking.json"
OUTPUT = "runtime/research/a39_a33_blocker_diagnostics"


def _load(root: Path) -> dict[str, Any]:
    path = root / SOURCE
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise FileNotFoundError(f"A33 report unavailable: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError("A33 report must be a JSON object")
    return value


def _candidate(row: dict[str, Any]) -> dict[str, Any]:
    reasons = [str(value) for value in row.get("eligibility_reasons", ())]
    return {key: row.get(key) for key in (
        "rank", "timeframe", "pattern", "direction", "tp_points", "sl_points",
        "max_holding_bars", "samples", "win_rate_pct", "expectancy_r",
        "profit_factor", "max_drawdown_r", "walk_forward_passes",
        "walk_forward_windows", "planned_rr", "minimum_win_rate_for_rr_pct",
        "metric_gate_pass", "eligibility",
    )} | {"eligibility_reasons": reasons, "blocker_count": len(reasons)}


def build_report(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    source = _load(root)
    rankings = source.get("rankings", {})
    balanced = rankings.get("balanced", ()) if isinstance(rankings, dict) else ()
    rows = [dict(row) for row in balanced if isinstance(row, dict)]
    blockers = Counter(str(reason) for row in rows for reason in row.get("eligibility_reasons", ()))
    eligible = [row for row in rows if row.get("eligibility") == "ELIGIBLE"]
    metric_pass = [row for row in rows if row.get("metric_gate_pass") is True]
    walk_forward_pass = [row for row in rows
                         if int(row.get("walk_forward_passes") or 0) >= 3
                         and int(row.get("walk_forward_windows") or 0) >= 4]
    nearest = sorted((row for row in rows if row.get("eligibility") != "ELIGIBLE"),
                     key=lambda row: (len(row.get("eligibility_reasons", ())),
                                      -int(row.get("walk_forward_passes") or 0),
                                      -float(row.get("expectancy_r") or 0),
                                      -float(row.get("profit_factor") or 0)))
    status = "ELIGIBLE_ROWS_AVAILABLE_FOR_MANUAL_REVIEW" if eligible else "A33_RESEARCH_ELIGIBILITY_BLOCKED"
    return {
        "schema": "afip.a39.a33_blocker_diagnostics.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source": SOURCE,
        "summary": {
            "balanced_rows": len(rows),
            "metric_gate_pass_rows": len(metric_pass),
            "walk_forward_3_of_4_rows": len(walk_forward_pass),
            "eligible_rows": len(eligible),
        },
        "blocker_counts": [{"reason": reason, "rows": count}
                           for reason, count in blockers.most_common()],
        "metric_gate_pass_candidates": [_candidate(row) for row in metric_pass[:100]],
        "walk_forward_pass_candidates": [_candidate(row) for row in walk_forward_pass[:100]],
        "nearest_blocked_candidates": [_candidate(row) for row in nearest[:25]],
        "next_required_action": ("MANUAL_REVIEW_ONLY_NO_EXECUTION_AUTHORITY" if eligible
                                 else "COLLECT_NEW_CLOSED_EVIDENCE_AND_RERUN_CHRONOLOGICAL_WALK_FORWARD"),
        "threshold_change_authorized": False,
        "profile_strategy_selection": "NOT_DECIDED",
        "automatic_profile_assignment": False,
        "demo_order_authorized": False,
        "live_order_authorized": False,
        "execution_authority": "NONE",
        "orders_sent": False,
        "truth_notice": "A39 explains persisted A33 results; it never changes thresholds or eligibility.",
    }


def render_html(report: dict[str, Any]) -> str:
    summary = report["summary"]
    metrics = "".join(f'<div class="metric"><small>{escape(label)}</small><strong>{value:,}</strong></div>'
                      for label, value in (("Balanced rows", summary["balanced_rows"]),
                      ("Metric gate pass", summary["metric_gate_pass_rows"]),
                      ("Walk-forward 3/4", summary["walk_forward_3_of_4_rows"]),
                      ("Eligible", summary["eligible_rows"])))
    blocker_rows = "".join(f'<tr><td>{escape(item["reason"])}</td><td>{item["rows"]:,}</td></tr>'
                           for item in report["blocker_counts"])
    cards = []
    for row in report["nearest_blocked_candidates"]:
        reasons = ", ".join(row["eligibility_reasons"]) or "NONE"
        cards.append(f'''<article><h3>🔎 Rank {row.get("rank")} · {escape(str(row.get("pattern")))}</h3>
<p>{escape(str(row.get("timeframe")))} · {escape(str(row.get("direction")))} · RR 1:{row.get("planned_rr")}</p>
<p>Samples {row.get("samples")} · Win {row.get("win_rate_pct")}% · Expectancy {row.get("expectancy_r")}R · PF {row.get("profit_factor")}</p>
<p>DD {row.get("max_drawdown_r")}R · Walk-forward {row.get("walk_forward_passes")}/{row.get("walk_forward_windows")}</p>
<p class="blocked"><b>Blocked:</b> {escape(reasons)}</p></article>''')
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>A39 A33 Blocker Diagnostics</title>
<style>*{{box-sizing:border-box}}body{{font:15px system-ui;background:#eef3f8;color:#14243a;margin:0}}main{{max-width:1250px;margin:auto;padding:24px}}header,.panel,article{{background:#fff;border:1px solid #d5dfe9;border-radius:14px;padding:18px;margin:14px 0}}.metrics,.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}}.metric{{background:#f2f6fa;padding:13px;border-radius:10px}}.metric strong{{display:block;font-size:24px}}article{{margin:0;border-left:6px solid #d69a21}}article p{{margin:7px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border:1px solid #dbe3eb;text-align:left}}.blocked{{background:#fff0dc;padding:9px;border-radius:8px}}</style></head><body><main>
<header><h1>🧪 A39 A33 Eligibility Blocker Diagnostics</h1><h2>{escape(report["status"])}</h2><p>{escape(report["truth_notice"])}</p><p>P1–P4 NOT_DECIDED · Demo false · Live false · Execution authority NONE</p></header>
<section class="panel"><h2>Evidence summary</h2><div class="metrics">{metrics}</div><p><b>Next:</b> {escape(report["next_required_action"])}</p></section>
<section class="panel"><h2>Blocker frequency</h2><table><thead><tr><th>Blocker</th><th>Rows</th></tr></thead><tbody>{blocker_rows}</tbody></table></section>
<section><h2>Nearest blocked candidates</h2><div class="cards">{''.join(cards)}</div></section>
</main></body></html>'''


def write_outputs(report: dict[str, Any], project_root: str | Path) -> tuple[Path, Path]:
    directory = Path(project_root).resolve() / OUTPUT
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "a39_a33_blocker_diagnostics.json"
    html_path = directory / "a39_a33_blocker_diagnostics.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    return json_path, html_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain persisted A33 eligibility blockers")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    report = build_report(args.project_root)
    json_path, html_path = write_outputs(report, args.project_root)
    print(json.dumps({"status": report["status"], "summary": report["summary"],
                      "json": str(json_path), "html": str(html_path),
                      "execution_authority": "NONE"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
