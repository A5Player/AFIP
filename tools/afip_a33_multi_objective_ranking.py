from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "afip.a33.multi_objective_ranking.v1"
POLICY = {
    "minimum_sl_points": 500,
    "minimum_net_expectancy_r": 0.15,
    "minimum_profit_factor": 1.30,
    "minimum_blind_samples": 100,
    "balanced_max_drawdown_r": 10.0,
    "defense_max_drawdown_r": 6.0,
    "required_walk_forward_passes": 3,
    "required_walk_forward_windows": 4,
}


def minimum_win_rate_for_rr(rr: float) -> float | None:
    if rr >= 4.0:
        return 27.0
    if rr >= 3.0:
        return 32.0
    if rr >= 2.0:
        return 42.0
    if rr >= 1.5:
        return 50.0
    if rr >= 1.0:
        return 60.0
    return None


def evaluate(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    sl = float(item.get("sl_points") or 0)
    tp = float(item.get("tp_points") or 0)
    rr = tp / sl if sl > 0 else 0.0
    required_win = minimum_win_rate_for_rr(rr)
    reasons: list[str] = []
    if sl < POLICY["minimum_sl_points"]:
        reasons.append("SL_BELOW_500_POINTS")
    if required_win is None:
        reasons.append("RR_BELOW_1_TO_1")
    elif float(item.get("win_rate_pct") or 0) < required_win:
        reasons.append("WIN_RATE_BELOW_RR_SAFETY_THRESHOLD")
    if float(item.get("expectancy_r") or 0) < POLICY["minimum_net_expectancy_r"]:
        reasons.append("NET_EXPECTANCY_BELOW_0_15R")
    pf = item.get("profit_factor")
    if pf is None or float(pf) < POLICY["minimum_profit_factor"]:
        reasons.append("PROFIT_FACTOR_BELOW_1_30")
    if int(item.get("samples") or 0) < POLICY["minimum_blind_samples"]:
        reasons.append("BLIND_SAMPLES_BELOW_100")
    if float(item.get("max_drawdown_r") or 0) > POLICY["balanced_max_drawdown_r"]:
        reasons.append("DRAWDOWN_ABOVE_10R")

    walk_passes = item.get("walk_forward_passes")
    walk_windows = item.get("walk_forward_windows")
    metrics_pass = not reasons
    if walk_passes is None or walk_windows is None:
        status = "PENDING_WALK_FORWARD" if metrics_pass else "NOT_ELIGIBLE"
        if metrics_pass:
            reasons.append("WALK_FORWARD_3_OF_4_REQUIRED")
    elif int(walk_passes) < POLICY["required_walk_forward_passes"] or int(walk_windows) < POLICY["required_walk_forward_windows"]:
        status = "NOT_ELIGIBLE"
        reasons.append("WALK_FORWARD_BELOW_3_OF_4")
    else:
        status = "ELIGIBLE" if metrics_pass else "NOT_ELIGIBLE"
    item.update({
        "planned_rr": round(rr, 4),
        "minimum_win_rate_for_rr_pct": required_win,
        "metric_gate_pass": metrics_pass,
        "eligibility": status,
        "eligibility_reasons": reasons,
    })
    return item


def _priority(row: dict[str, Any]) -> int:
    return {"ELIGIBLE": 2, "PENDING_WALK_FORWARD": 1, "NOT_ELIGIBLE": 0}.get(row["eligibility"], 0)


def build_report(a32: dict[str, Any]) -> dict[str, Any]:
    if a32.get("execution_authority") != "NONE":
        raise ValueError("A32 execution authority must be NONE")
    rows = [evaluate(row) for row in a32.get("rows", [])]
    accepted = [row for row in rows if float(row.get("sl_points") or 0) >= POLICY["minimum_sl_points"]]
    rankings = {
        "balanced": sorted(accepted, key=lambda r: (_priority(r), r["expectancy_r"], r["profit_factor"] or 0,
                                                       -r["max_drawdown_r"], r["win_rate_pct"], r["samples"]), reverse=True),
        "high_win_rate": sorted(accepted, key=lambda r: (_priority(r), r["win_rate_pct"], r["profit_factor"] or 0,
                                                            r["expectancy_r"], -r["max_drawdown_r"], r["samples"]), reverse=True),
        "capital_growth": sorted(accepted, key=lambda r: (_priority(r), r["expectancy_r"], r["profit_factor"] or 0,
                                                             r["win_rate_pct"], -r["max_drawdown_r"], r["samples"]), reverse=True),
        "capital_defense": sorted(accepted, key=lambda r: (_priority(r), -r["max_drawdown_r"], r["win_rate_pct"],
                                                              r["profit_factor"] or 0, r["expectancy_r"], r["samples"]), reverse=True),
    }
    for values in rankings.values():
        for rank, row in enumerate(values, 1):
            row.setdefault("ranking_positions", {})
            row["ranking_positions"][next(name for name, candidate in rankings.items() if candidate is values)] = rank
    return {
        "schema": SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_schema": a32.get("schema"),
        "source_generated_at_utc": a32.get("generated_at_utc"),
        "execution_authority": "NONE",
        "profile_strategy_selection": "NOT_DECIDED",
        "default_ranking": "BALANCED",
        "policy": POLICY,
        "truth_notice": "No row is ELIGIBLE until real walk-forward evidence passes at least 3 of 4 windows.",
        "source_rows": len(rows),
        "sl_500_or_more_rows": len(accepted),
        "metric_gate_pass_rows": sum(row["metric_gate_pass"] for row in accepted),
        "eligible_rows": sum(row["eligibility"] == "ELIGIBLE" for row in accepted),
        "pending_walk_forward_rows": sum(row["eligibility"] == "PENDING_WALK_FORWARD" for row in accepted),
        "rankings": rankings,
    }


def _card(row: dict[str, Any], rank: int) -> str:
    pf = "ไม่มีข้อมูล" if row.get("profit_factor") is None else f'{row["profit_factor"]:.2f}'
    reasons = ", ".join(row["eligibility_reasons"]) or "ผ่านเกณฑ์ทั้งหมด"
    status_class = {"ELIGIBLE": "pass", "PENDING_WALK_FORWARD": "pending"}.get(row["eligibility"], "fail")
    return f'''<article class="card {status_class}"><h3>🏆 อันดับ {rank} · {html.escape(str(row.get("pattern", "UNKNOWN")))}</h3>
<div class="grid"><p>🕒 <b>Timeframe</b><br>{row.get("timeframe")}</p><p>🧭 <b>ทิศทาง</b><br>{row.get("direction")}</p><p>⚖️ <b>RR ที่วางแผน</b><br>1:{row["planned_rr"]:.2f}</p><p>🧪 <b>Blind-forward</b><br>{row.get("samples", 0):,} รายการ</p></div>
<div class="grid"><p>🛡️ <b>SL</b><br>{row.get("sl_points", 0):,} จุด</p><p>🎯 <b>TP</b><br>{row.get("tp_points", 0):,} จุด</p><p>⏳ <b>ถือสูงสุด</b><br>{row.get("max_holding_bars", 0)} แท่ง</p><p>⌛ <b>ถือเฉลี่ย</b><br>{row.get("average_holding_bars", 0):.2f} แท่ง</p></div>
<div class="grid"><p>✅ <b>Win rate</b><br>{row.get("win_rate_pct", 0):.2f}%</p><p>📈 <b>Expectancy สุทธิ</b><br>{row.get("expectancy_r", 0):+.3f}R</p><p>💹 <b>Profit factor</b><br>{pf}</p><p>📉 <b>Max drawdown</b><br>{row.get("max_drawdown_r", 0):.2f}R</p></div>
<p class="status"><b>สถานะ: {row["eligibility"]}</b><br><span>{html.escape(reasons)}</span></p></article>'''


def write_outputs(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "a33_multi_objective_ranking.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    labels = {
        "balanced": "⚖️ Balanced (ค่าเริ่มต้น)",
        "high_win_rate": "✅ High Win Rate",
        "capital_growth": "💰 Capital Growth",
        "capital_defense": "🛡️ Capital Defense",
    }
    nav = "".join(f'<a href="#{name}">{label}</a>' for name, label in labels.items())
    sections = []
    for name, label in labels.items():
        cards = "".join(_card(row, rank) for rank, row in enumerate(report["rankings"][name][:100], 1))
        sections.append(f'<section id="{name}"><h2>{label}</h2>{cards or "<p>ไม่มีข้อมูล</p>"}</section>')
    document = f'''<!doctype html><html lang="th"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>AFIP A33 Multi-Objective Ranking</title>
<style>*{{box-sizing:border-box}}body{{font:16px system-ui;margin:0;background:#eef3f8;color:#14233a}}main{{max-width:1180px;margin:auto;padding:24px}}nav{{position:sticky;top:0;background:#10243f;padding:12px;border-radius:12px;z-index:2}}nav a{{display:inline-block;color:white;text-decoration:none;padding:10px 14px}}.notice,.card{{background:white;border:1px solid #d6e0ea;border-radius:15px;padding:18px;margin:14px 0;box-shadow:0 4px 14px #1231}}.card{{border-left:7px solid #aab4c0}}.card.pending{{border-left-color:#e5a922}}.card.pass{{border-left-color:#24a36a}}.card.fail{{opacity:.78}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}.grid p{{background:#f5f8fb;padding:12px;border-radius:10px;margin:3px}}.status{{padding:12px;background:#fff4d7;border-radius:10px}}h2{{margin-top:36px}}@media(max-width:720px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}</style>
<main><h1>📊 AFIP A33 Multi-Objective Ranking</h1><div class="notice"><b>Default: BALANCED · SL ขั้นต่ำ 500 จุด</b><p>Metric gate ผ่าน {report["metric_gate_pass_rows"]:,} · รอ Walk-forward {report["pending_walk_forward_rows"]:,} · ELIGIBLE จริง {report["eligible_rows"]:,}</p><p>⚠️ P1–P4 = NOT_DECIDED · Execution authority = NONE</p></div><nav>{nav}</nav>{''.join(sections)}</main></html>'''
    (output_dir / "a33_multi_objective_ranking.html").write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP A33 multi-objective ranking")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.project_root.resolve()
    source = root / "runtime/research/a32_real_backtest/a32_real_backtest_campaign.json"
    if not source.exists():
        raise FileNotFoundError(f"Run A32 first; missing {source}")
    a32 = json.loads(source.read_text(encoding="utf-8"))
    report = build_report(a32)
    output = root / "runtime/research/a33_multi_objective_ranking"
    write_outputs(report, output)
    print(json.dumps({key: report[key] for key in ("default_ranking", "source_rows", "sl_500_or_more_rows",
                                                    "metric_gate_pass_rows", "pending_walk_forward_rows",
                                                    "eligible_rows", "execution_authority")}, indent=2))
    print(f"A33 JSON: {output / 'a33_multi_objective_ranking.json'}")
    print(f"A33 HTML: {output / 'a33_multi_objective_ranking.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
