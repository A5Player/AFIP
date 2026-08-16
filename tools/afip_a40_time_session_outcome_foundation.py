"""Normalize scored closed outcomes for chronological day/time/session research."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
import math
from pathlib import Path
from typing import Any

from afip.historical_replay_research import AppendOnlyResearchDataset


OUTPUT = "runtime/research/a40_time_session_outcomes"


def _time(value: Any) -> datetime | None:
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return result.astimezone(timezone.utc) if result.tzinfo is not None else None


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _identity(row: dict[str, Any]) -> str:
    source = "|".join(str(row.get(key, "")) for key in (
        "decision_timestamp_utc", "research_case_id", "policy_id", "timeframe",
        "pattern_family", "session_name"))
    return "A40-" + sha256(source.encode()).hexdigest()[:20].upper()


def build_report(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    dataset = AppendOnlyResearchDataset(root / "runtime/research")
    envelopes = dataset.records("a22_holding_exit_validation_observations")
    rejected = Counter()
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for envelope in envelopes:
        row = dict(envelope.get("record", {}))
        if str(row.get("research_case_id", "")).startswith("A41-") and row.get("selection_policy_version") != "A41_V2_DEDUP_CONF60_COOLDOWN24":
            rejected["A41_V1_SUPERSEDED_NO_SELECTION_PROVENANCE"] += 1
            continue
        stamp = _time(row.get("decision_timestamp_utc"))
        result_r = _number(row.get("net_realized_r"))
        if stamp is None:
            rejected["DECISION_TIMESTAMP_MISSING_OR_NOT_UTC"] += 1
            continue
        if result_r is None:
            rejected["NET_REALIZED_R_MISSING"] += 1
            continue
        if row.get("future_data_used") is True:
            rejected["FUTURE_DATA_USED"] += 1
            continue
        if row.get("outcome_evaluation_uses_subsequent_closed_bars") is not True:
            rejected["CLOSED_BAR_PROVENANCE_NOT_CONFIRMED"] += 1
            continue
        required = {key: str(row.get(key, "")).strip() for key in (
            "policy_id", "timeframe", "pattern_family", "market_regime", "session_name")}
        missing = [key for key, value in required.items() if not value]
        if missing:
            rejected["CONTEXT_FIELDS_MISSING"] += 1
            continue
        item = {
            "outcome_id": "",
            "decision_timestamp_utc": stamp.isoformat().replace("+00:00", "Z"),
            "calendar_day_utc": stamp.date().isoformat(),
            "weekday_utc": stamp.strftime("%A").upper(),
            "hour_utc": stamp.hour,
            "session_name": required["session_name"],
            "session_source": "RECORDED_A22_CONTEXT",
            "event_window": str(row.get("event_window", "UNCLASSIFIED")),
            "calendar_context": str(row.get("calendar_context", "UNCLASSIFIED")),
            "timeframe": required["timeframe"],
            "pattern_family": required["pattern_family"],
            "market_regime": required["market_regime"],
            "direction": str(row.get("direction", "UNCLASSIFIED")),
            "policy_id": required["policy_id"],
            "research_case_id": str(row.get("research_case_id", "UNCLASSIFIED")),
            "candidate_group_id": str(row.get("candidate_group_id", row.get("research_case_id", "UNCLASSIFIED"))),
            "policy_variant_is_independent_trade": bool(row.get("policy_variant_is_independent_trade", False)),
            "selection_policy_version": str(row.get("selection_policy_version", "LEGACY_NON_A41_SOURCE")),
            "decision_score_percent": _number(row.get("decision_score_percent")),
            "net_realized_r": result_r,
            "mfe_r": _number(row.get("mfe_r")),
            "mae_r": _number(row.get("mae_r")),
            "holding_seconds": _number(row.get("holding_seconds")),
            "position_units": int(row.get("position_units", 1) or 1),
            "broker_order_count": int(row.get("broker_order_count", 1) or 1),
            "research_only": True,
            "execution_authority": "NONE",
        }
        item["outcome_id"] = _identity(item)
        if item["outcome_id"] in seen:
            rejected["DUPLICATE_OUTCOME_ID"] += 1
            continue
        seen.add(item["outcome_id"])
        normalized.append(item)
    normalized.sort(key=lambda row: (row["decision_timestamp_utc"], row["outcome_id"]))
    count = len(normalized)
    train_end = int(count * .6)
    validation_end = int(count * .8)
    for index, row in enumerate(normalized):
        row["chronological_partition"] = ("TRAIN" if index < train_end else
                                            "VALIDATION" if index < validation_end else "BLIND_FORWARD")
    coverage = {
        "weekdays": dict(sorted(Counter(row["weekday_utc"] for row in normalized).items())),
        "hours_utc": {str(key): value for key, value in sorted(Counter(row["hour_utc"] for row in normalized).items())},
        "sessions": dict(sorted(Counter(row["session_name"] for row in normalized).items())),
        "timeframes": dict(sorted(Counter(row["timeframe"] for row in normalized).items())),
        "patterns": dict(sorted(Counter(row["pattern_family"] for row in normalized).items())),
        "regimes": dict(sorted(Counter(row["market_regime"] for row in normalized).items())),
    }
    status = "READY_FOR_SELECTIVE_RANKING_RESEARCH" if normalized else "WAITING_FOR_SCORED_CLOSED_OUTCOMES"
    return {
        "schema": "afip.a40.time_session_outcome_foundation.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_dataset": "a22_holding_exit_validation_observations",
        "source_records": len(envelopes),
        "usable_closed_outcomes": count,
        "rejected_records": sum(rejected.values()),
        "rejection_reasons": dict(rejected),
        "partition_method": "CHRONOLOGICAL_60_20_20_NO_SHUFFLE",
        "partitions": dict(Counter(row["chronological_partition"] for row in normalized)),
        "coverage": coverage,
        "normalized_outcomes": normalized,
        "next_required_action": ("BUILD_STANDARD_BALANCED_SESSION_AND_ULTIMATE_RANKINGS" if normalized
                                 else "CONTINUE_COLLECTING_SCORED_CLOSED_OUTCOMES"),
        "no_trade_is_valid": True,
        "profile_strategy_selection": "NOT_DECIDED",
        "automatic_profile_assignment": False,
        "demo_order_authorized": False,
        "live_order_authorized": False,
        "execution_authority": "NONE",
        "orders_sent": False,
    }


def render_html(report: dict[str, Any]) -> str:
    coverage = report["coverage"]
    sections = []
    for name in ("weekdays", "hours_utc", "sessions", "timeframes", "patterns", "regimes"):
        rows = "".join(f"<tr><td>{escape(str(key))}</td><td>{value}</td></tr>"
                       for key, value in coverage[name].items())
        sections.append(f'<article><h2>{escape(name.replace("_", " ").title())}</h2><table><tr><th>Segment</th><th>Outcomes</th></tr>{rows or "<tr><td colspan=2>NO EVIDENCE</td></tr>"}</table></article>')
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>A40 Time Session Foundation</title>
<style>body{{font:15px system-ui;background:#eef3f8;color:#14243a;margin:0}}main{{max-width:1250px;margin:auto;padding:24px}}header,article{{background:white;border:1px solid #d6e0ea;border-radius:14px;padding:18px;margin:14px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #dbe3eb;padding:8px;text-align:left}}</style></head><body><main>
<header><h1>🕒 A40 Chronological Time/Session Outcome Foundation</h1><h2>{escape(report["status"])}</h2><p>Source {escape(report["source_dataset"])} · usable {report["usable_closed_outcomes"]} · rejected {report["rejected_records"]}</p><p>Chronological 60/20/20 · no shuffle · recorded session context only · no inferred profitability.</p><p>No-trade valid · P1–P4 NOT_DECIDED · Demo false · Live false · Execution authority NONE</p><p><b>Next:</b> {escape(report["next_required_action"])}</p></header><section class="grid">{''.join(sections)}</section>
</main></body></html>'''


def write_outputs(report: dict[str, Any], project_root: str | Path) -> tuple[Path, Path, Path]:
    directory = Path(project_root).resolve() / OUTPUT
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "a40_time_session_foundation.json"
    jsonl_path = directory / "a40_normalized_closed_outcomes.jsonl"
    html_path = directory / "a40_time_session_foundation.html"
    summary = dict(report); outcomes = summary.pop("normalized_outcomes")
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    jsonl_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in outcomes), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    return json_path, jsonl_path, html_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build A40 chronological day/time/session evidence")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    report = build_report(args.project_root)
    paths = write_outputs(report, args.project_root)
    print(json.dumps({"status": report["status"], "source_records": report["source_records"],
                      "usable_closed_outcomes": report["usable_closed_outcomes"],
                      "outputs": [str(path) for path in paths], "execution_authority": "NONE"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
