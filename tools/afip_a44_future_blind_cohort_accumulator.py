"""A44 prospective, sealed future blind cohort accumulator.

The accumulator never selects a rule.  It accepts only the winner frozen by
A43 before the prospective cutoff, stores matching closed outcomes, and keeps
all performance metrics sealed until the minimum independent-day cohort is
complete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

OUTPUT = "runtime/research/a44_future_blind_cohort_accumulator"
MINIMUM_COHORT_DAYS = 15
SOURCE_POLICY_VERSION = "A41_V2_DEDUP_CONF60_COOLDOWN24"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _parse_utc(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _canonical_signature(winner: dict[str, Any], cutoff: str) -> str:
    frozen = {
        "schema": "afip.a44.future_blind_cohort_accumulator.v1",
        "cutoff_timestamp_utc": cutoff,
        "source_policy_version": SOURCE_POLICY_VERSION,
        "rule_id": winner.get("rule_id"),
        "dimension": winner.get("dimension"),
        "key": winner.get("key"),
        "policy_id": winner.get("policy_id"),
        "daily_selection": "FIRST_MATCH_CHRONOLOGICALLY_PER_UTC_DAY",
        "minimum_cohort_days": MINIMUM_COHORT_DAYS,
    }
    payload = json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _matches(row: dict[str, Any], winner: dict[str, Any]) -> bool:
    key = str(winner.get("key", ""))
    policy, value = key.split("|", 1) if "|" in key else (key, "")
    if str(row.get("policy_id")) != policy:
        return False
    mapping = {
        "POLICY_TIMEFRAME": str(row.get("timeframe")),
        "POLICY_SESSION": str(row.get("session_name")),
        "POLICY_WEEKDAY": str(row.get("weekday_utc")),
        "POLICY_HOUR_UTC": str(row.get("hour_utc")),
        "POLICY_DIRECTION": str(row.get("direction")),
    }
    return winner.get("dimension") == "POLICY" or mapping.get(str(winner.get("dimension"))) == value


def _load_source_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("selection_policy_version") == SOURCE_POLICY_VERSION:
            rows.append(row)
    return rows


def _safe_identity(row: dict[str, Any]) -> str:
    return f'{row.get("candidate_group_id", "")}|{row.get("policy_id", "")}'


def _sealed_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    days = sorted({str(row.get("calendar_day_utc")) for row in rows if row.get("calendar_day_utc")})
    complete = len(days) >= MINIMUM_COHORT_DAYS
    return {
        "status": "COHORT_COMPLETE_METRICS_READY_FOR_A43_AUDIT" if complete else "SEALED_ACCUMULATING",
        "accepted_closed_outcomes": len(rows),
        "independent_trading_days": len(days),
        "minimum_required_days": MINIMUM_COHORT_DAYS,
        "remaining_days": max(0, MINIMUM_COHORT_DAYS - len(days)),
        "first_day_utc": days[0] if days else None,
        "latest_day_utc": days[-1] if days else None,
        "metrics_sealed": not complete,
        "win_rate_pct": None,
        "expectancy_r": None,
        "profit_factor": None,
        "max_drawdown_r": None,
    }


def build_report(project_root: str | Path, now_utc: datetime | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    root = Path(project_root).resolve()
    out = root / OUTPUT
    previous = _load_json(out / "a44_future_blind_cohort_accumulator.json")
    a43 = _load_json(root / "runtime/research/a43_ultimate_selective_setup_validation/a43_ultimate_selective_setup_validation.json")
    winner = a43.get("frozen_winner") if isinstance(a43.get("frozen_winner"), dict) else None
    winner_id = a43.get("frozen_winner_rule_id")
    generated = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()

    if not winner or not winner_id:
        report = {
            "schema": "afip.a44.future_blind_cohort_accumulator.v1",
            "generated_at_utc": generated,
            "status": "BLOCKED_NO_PREBLIND_FROZEN_WINNER",
            "source_a43_status": a43.get("status", "MISSING"),
            "frozen_winner_rule_id": None,
            "cutoff_timestamp_utc": None,
            "source_contract_signature_sha256": None,
            "cohort": _sealed_summary([]),
            "metrics_release_condition": "AT_LEAST_15_INDEPENDENT_UTC_TRADING_DAYS",
            "historical_exposed_blind_reused": False,
            "future_only": True,
            "final_research_recommendation": "NO_TRADE",
            "demo_order_authorized": False,
            "live_order_authorized": False,
            "execution_authority": "NONE",
            "orders_sent": False,
        }
        return report, []

    previous_winner = previous.get("frozen_winner_rule_id")
    if previous_winner and previous_winner != winner_id:
        report = dict(previous)
        report.update({"generated_at_utc": generated, "status": "BLOCKED_FROZEN_WINNER_CHANGED",
                       "observed_a43_winner_rule_id": winner_id, "final_research_recommendation": "NO_TRADE",
                       "execution_authority": "NONE"})
        return report, []

    cutoff = str(previous.get("cutoff_timestamp_utc") or generated)
    signature = _canonical_signature(winner, cutoff)
    if previous.get("source_contract_signature_sha256") not in (None, signature):
        report = dict(previous)
        report.update({"generated_at_utc": generated, "status": "BLOCKED_SOURCE_CONTRACT_SIGNATURE_CHANGED",
                       "observed_source_contract_signature_sha256": signature,
                       "final_research_recommendation": "NO_TRADE", "execution_authority": "NONE"})
        return report, []

    cutoff_dt = _parse_utc(cutoff)
    source = _load_source_rows(root / "runtime/research/a40_time_session_outcomes/a40_normalized_closed_outcomes.jsonl")
    eligible = [row for row in source if (ts := _parse_utc(row.get("decision_timestamp_utc"))) is not None
                and cutoff_dt is not None and ts > cutoff_dt and _matches(row, winner)]
    # Enforce the frozen zero-to-one rule without using outcome values: first
    # chronological matching candidate per UTC day.
    first_by_day: dict[str, dict[str, Any]] = {}
    for row in sorted(eligible, key=lambda item: (str(item.get("decision_timestamp_utc")), str(item.get("candidate_group_id")))):
        day = str(row.get("calendar_day_utc", ""))
        if day and day not in first_by_day:
            first_by_day[day] = row
    accepted = list(first_by_day.values())
    summary = _sealed_summary(accepted)
    report = {
        "schema": "afip.a44.future_blind_cohort_accumulator.v1",
        "generated_at_utc": generated,
        "status": summary["status"],
        "source_a43_status": a43.get("status", "MISSING"),
        "frozen_winner_rule_id": winner_id,
        "frozen_winner_rule": {key: winner.get(key) for key in ("rule_id", "dimension", "key", "policy_id", "planned_rr", "minimum_sl_points_observed")},
        "cutoff_timestamp_utc": cutoff,
        "source_contract_signature_sha256": signature,
        "source_policy_version": SOURCE_POLICY_VERSION,
        "cohort": summary,
        "selection": "FIRST_MATCH_CHRONOLOGICALLY_PER_UTC_DAY",
        "metrics_release_condition": "AT_LEAST_15_INDEPENDENT_UTC_TRADING_DAYS",
        "historical_exposed_blind_reused": False,
        "future_only": True,
        "final_research_recommendation": "NO_TRADE",
        "demo_order_authorized": False,
        "live_order_authorized": False,
        "execution_authority": "NONE",
        "orders_sent": False,
    }
    return report, accepted


def write_outputs(report: dict[str, Any], accepted: list[dict[str, Any]], project_root: str | Path) -> tuple[Path, Path, Path]:
    out = Path(project_root).resolve() / OUTPUT
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "a44_future_blind_cohort_accumulator.json"
    rows_path = out / "a44_sealed_future_blind_cohort.jsonl"
    html_path = out / "a44_future_blind_cohort_accumulator.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in accepted), encoding="utf-8")
    cohort = report["cohort"]
    html_path.write_text(f'''<!doctype html><meta charset="utf-8"><title>A44 Future Blind Cohort</title><style>body{{font:14px system-ui;background:#edf2f7;color:#14243a}}main{{max-width:1100px;margin:auto}}article{{background:white;padding:20px;margin:18px;border-radius:14px}}dt{{font-weight:700}}dd{{margin-bottom:12px}}</style><main><article><h1>A44 Future Blind Cohort Accumulator</h1><h2>{escape(str(report['status']))}</h2><dl><dt>Frozen winner</dt><dd>{escape(str(report.get('frozen_winner_rule_id')))}</dd><dt>Prospective cutoff</dt><dd>{escape(str(report.get('cutoff_timestamp_utc')))}</dd><dt>Independent days</dt><dd>{cohort['independent_trading_days']} / {cohort['minimum_required_days']}</dd><dt>Remaining days</dt><dd>{cohort['remaining_days']}</dd><dt>Metrics sealed</dt><dd>{cohort['metrics_sealed']}</dd><dt>Authority</dt><dd>NONE — NO_TRADE</dd></dl><p>Historical exposed Blind is never reused. Performance metrics remain hidden until the frozen cohort reaches 15 independent UTC trading days.</p></article></main>''', encoding="utf-8")
    return json_path, rows_path, html_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    report, accepted = build_report(args.project_root)
    paths = write_outputs(report, accepted, args.project_root)
    print(json.dumps({"status": report["status"], "frozen_winner_rule_id": report.get("frozen_winner_rule_id"),
                      "cutoff_timestamp_utc": report.get("cutoff_timestamp_utc"), "cohort": report["cohort"],
                      "outputs": [str(path) for path in paths], "execution_authority": "NONE"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
