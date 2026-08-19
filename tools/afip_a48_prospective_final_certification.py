"""A48 fail-closed final audit for the A45 winner and A44 future Blind cohort."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any

OUTPUT = "runtime/research/a48_prospective_final_certification"
MINIMUM_BLIND_DAYS = 15
MAX_DRAWDOWN_R = 10.0


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            result.append(row)
    return result


def _profit_factor(value: Any) -> float:
    return 10.0 if value == "INFINITE" else float(value or 0)


def _win_threshold(rr: float) -> float:
    if rr >= 4:
        return 27
    if rr >= 3:
        return 32
    if rr >= 2:
        return 42
    if rr >= 1.5:
        return 50
    return 60


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (str(row.get("decision_timestamp_utc")), str(row.get("candidate_group_id"))))
    pnl = [float(row.get("net_realized_r") or 0) for row in ordered]
    wins = sum(value > 0 for value in pnl)
    gross_win = sum(value for value in pnl if value > 0)
    gross_loss = -sum(value for value in pnl if value < 0)
    equity = peak = drawdown = 0.0
    for value in pnl:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return {
        "samples": len(pnl),
        "independent_trading_days": len({str(row.get("calendar_day_utc")) for row in ordered if row.get("calendar_day_utc")}),
        "win_rate_pct": round(100 * wins / len(pnl), 6) if pnl else None,
        "expectancy_r": round(mean(pnl), 8) if pnl else None,
        "profit_factor": round(gross_win / gross_loss, 8) if gross_loss else ("INFINITE" if gross_win else None),
        "max_drawdown_r": round(drawdown, 8),
        "net_result_r": round(sum(pnl), 8),
    }


def build_report(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    a45 = _json(root / "runtime/research/a45_future_preblind_qualification/a45_future_preblind_qualification.json")
    a44 = _json(root / "runtime/research/a44_future_blind_cohort_accumulator/a44_future_blind_cohort_accumulator.json")
    winner_id = a45.get("frozen_preblind_winner_rule_id")
    cohort = a44.get("cohort") if isinstance(a44.get("cohort"), dict) else {}
    base = {
        "schema": "afip.a48.prospective_final_certification.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_a45_status": a45.get("status", "MISSING"),
        "source_a44_status": a44.get("status", "MISSING"),
        "frozen_preblind_winner_rule_id": winner_id,
        "a45_cutoff_timestamp_utc": a45.get("cutoff_timestamp_utc"),
        "a44_cutoff_timestamp_utc": a44.get("cutoff_timestamp_utc"),
        "historical_exposed_blind_reused": False,
        "blind_used_for_selection_or_reordering": False,
        "fallback_after_blind_failure": False,
        "research_only": True,
        "demo_order_authorized": False,
        "live_order_authorized": False,
        "execution_authority": "NONE",
        "orders_sent": False,
    }
    if a45.get("status") != "FROZEN_PREBLIND_WINNER_READY_FOR_NEW_BLIND" or not winner_id:
        return {**base, "status": "WAITING_FOR_A45_FROZEN_PREBLIND_WINNER", "blind_metrics": None,
                "audit_pass": None, "audit_reasons": ["A45_WINNER_NOT_READY"], "final_research_recommendation": "NO_TRADE"}
    if a44.get("frozen_winner_rule_id") != winner_id:
        return {**base, "status": "BLOCKED_A45_A44_WINNER_MISMATCH", "blind_metrics": None,
                "audit_pass": False, "audit_reasons": ["FROZEN_WINNER_ID_MISMATCH"], "final_research_recommendation": "NO_TRADE"}
    if a44.get("status") != "COHORT_COMPLETE_METRICS_READY_FOR_A43_AUDIT" or cohort.get("metrics_sealed") is not False:
        return {**base, "status": "SEALED_WAITING_FOR_A44_FUTURE_BLIND_COMPLETION", "blind_metrics": None,
                "blind_days": int(cohort.get("independent_trading_days") or 0),
                "remaining_blind_days": int(cohort.get("remaining_days") or MINIMUM_BLIND_DAYS),
                "audit_pass": None, "audit_reasons": ["FUTURE_BLIND_COHORT_INCOMPLETE"], "final_research_recommendation": "NO_TRADE"}
    rows = _rows(root / "runtime/research/a44_future_blind_cohort_accumulator/a44_sealed_future_blind_cohort.jsonl")
    metrics = _metrics(rows)
    winner = a45.get("frozen_preblind_winner") if isinstance(a45.get("frozen_preblind_winner"), dict) else {}
    rr = float(winner.get("planned_rr") or 0)
    reasons = []
    if metrics["independent_trading_days"] < MINIMUM_BLIND_DAYS: reasons.append("BLIND_DAYS_BELOW_15")
    if (metrics["expectancy_r"] or 0) <= 0: reasons.append("BLIND_EXPECTANCY_NOT_POSITIVE")
    if _profit_factor(metrics["profit_factor"]) < 1: reasons.append("BLIND_PROFIT_FACTOR_BELOW_1")
    if (metrics["win_rate_pct"] or 0) < _win_threshold(rr): reasons.append("BLIND_WIN_RATE_BELOW_RR_SAFETY_THRESHOLD")
    if metrics["max_drawdown_r"] > MAX_DRAWDOWN_R: reasons.append("BLIND_DRAWDOWN_ABOVE_10R")
    passed = not reasons
    return {**base, "status": "PROSPECTIVE_RESEARCH_CERTIFICATION_PASS" if passed else "NO_TRADE_PROSPECTIVE_BLIND_AUDIT_FAILED",
            "planned_rr": rr, "blind_metrics": metrics, "audit_pass": passed, "audit_reasons": reasons,
            "final_research_recommendation": "REVIEW_CERTIFIED_ULTIMATE_CANDIDATE" if passed else "NO_TRADE"}


def write_outputs(report: dict[str, Any], project_root: str | Path) -> tuple[Path, Path]:
    out = Path(project_root).resolve() / OUTPUT
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "a48_prospective_final_certification.json"
    html_path = out / "a48_prospective_final_certification.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(f'''<!doctype html><meta charset="utf-8"><title>A48 Prospective Final Certification</title><style>body{{font:14px system-ui;background:#edf2f7;color:#14243a}}main{{max-width:1100px;margin:auto;background:white;padding:20px;border-radius:14px}}dt{{font-weight:700}}dd{{margin-bottom:12px}}</style><main><h1>A48 Prospective Final Certification Gate</h1><h2>{escape(str(report["status"]))}</h2><dl><dt>Frozen winner</dt><dd>{escape(str(report.get("frozen_preblind_winner_rule_id")))}</dd><dt>Audit pass</dt><dd>{escape(str(report.get("audit_pass")))}</dd><dt>Reasons</dt><dd>{escape(", ".join(report.get("audit_reasons", ())))}</dd><dt>Recommendation</dt><dd>{escape(str(report.get("final_research_recommendation")))}</dd></dl><p>Future-only Blind · no fallback · NO_TRADE until PASS · execution authority NONE</p></main>''', encoding="utf-8")
    return json_path, html_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    report = build_report(args.project_root)
    paths = write_outputs(report, args.project_root)
    print(json.dumps({"status": report["status"], "frozen_preblind_winner_rule_id": report.get("frozen_preblind_winner_rule_id"),
                      "audit_pass": report.get("audit_pass"), "final_research_recommendation": report["final_research_recommendation"],
                      "outputs": [str(path) for path in paths], "execution_authority": "NONE"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
