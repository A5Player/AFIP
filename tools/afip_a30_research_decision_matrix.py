"""Build a truthful, profile-neutral AFIP research decision matrix."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

NA = "DATA_UNAVAILABLE"


def _records(path: Path) -> Iterable[Mapping[str, Any]]:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                value = value.get("record", value) if isinstance(value, Mapping) else None
                if isinstance(value, Mapping):
                    yield value
            except (ValueError, TypeError, json.JSONDecodeError):
                continue


def _mean(total: float, count: int) -> float | str:
    return round(total / count, 6) if count else NA


def _tf(value: Any) -> str:
    text = str(value or NA).upper()
    for token in ("M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"):
        if token in text.split("-") or f"GOLD-{token}-" in text:
            return token
    return text if text != "" else NA


def build_report(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    research = root / "runtime" / "research"
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    outcome_path = research / "automatic" / "schema_v2" / "adversarial_market_behaviour" / "outcomes.jsonl"
    for item in _records(outcome_path):
        key = (str(item.get("pattern_name") or "UNCLASSIFIED"), _tf(item.get("timeframe")),
               str(item.get("threat_state") or NA), str(item.get("entry_policy") or NA))
        row = grouped.setdefault(key, {"samples": 0, "up": 0.0, "down": 0.0, "whipsaw": 0,
                                       "follow": defaultdict(int), "horizon": defaultdict(int)})
        row["samples"] += 1
        for source, target in (("upward_excursion_atr", "up"), ("downward_excursion_atr", "down")):
            try: row[target] += float(item.get(source, 0.0))
            except (TypeError, ValueError): pass
        row["whipsaw"] += int(bool(item.get("whipsaw_observed")))
        row["follow"][str(item.get("follow_through_direction") or NA)] += 1
        row["horizon"][str(item.get("forward_horizon_bars") or NA)] += 1

    rows: list[dict[str, Any]] = []
    for (pattern, timeframe, threat, entry_policy), data in grouped.items():
        samples = data["samples"]
        dominant = max(data["follow"], key=data["follow"].get) if data["follow"] else NA
        rows.append({
            "evidence_tier": "C_OBSERVATIONAL_FORWARD_EXCURSION", "pattern": pattern,
            "timeframe": timeframe, "market_regime": threat, "direction": dominant,
            "entry_policy": entry_policy, "sl_atr_buffer": NA, "tp_atr_buffer": NA,
            "holding_time": f"{max(data['horizon'], key=data['horizon'].get)} CLOSED BARS" if data["horizon"] else NA,
            "samples": samples, "win_rate": NA, "expectancy_r": NA, "profit_factor": NA,
            "max_drawdown": NA, "average_mfe_atr": _mean(data["up"], samples),
            "average_mae_atr": _mean(data["down"], samples),
            "whipsaw_rate_percent": round(100.0 * data["whipsaw"] / samples, 4) if samples else NA,
            "walk_forward_status": NA, "blind_forward_status": "CLOSED_BAR_FORWARD_OBSERVATION",
            "eligibility": "RESEARCH_ONLY_NOT_ELIGIBLE_FOR_PROFILE_ASSIGNMENT",
            "reason": "No closed-position P/L evidence is joined to this exact segment.",
            "source_dataset": "automatic/schema_v2/adversarial_market_behaviour/outcomes.jsonl",
        })

    candidate_groups: dict[tuple[str, str, str], dict[str, float]] = defaultdict(lambda: {"samples": 0, "confidence": 0.0})
    candidate_path = research / "automatic" / "schema_v2" / "candidates.jsonl"
    for item in _records(candidate_path):
        key = (str(item.get("pattern_family") or "UNCLASSIFIED"), _tf(item.get("scenario_id")),
               str(item.get("direction") or NA))
        candidate_groups[key]["samples"] += 1
        try: candidate_groups[key]["confidence"] += float(item.get("confidence", 0.0))
        except (TypeError, ValueError): pass
    for (pattern, timeframe, direction), data in candidate_groups.items():
        samples = int(data["samples"])
        rows.append({
            "evidence_tier": "D_CANDIDATE_ONLY", "pattern": pattern, "timeframe": timeframe,
            "market_regime": NA, "direction": direction, "entry_policy": "AVAILABLE_EVIDENCE_ONLY",
            "sl_atr_buffer": NA, "tp_atr_buffer": NA, "holding_time": NA, "samples": samples,
            "win_rate": NA, "expectancy_r": NA, "profit_factor": NA, "max_drawdown": NA,
            "average_mfe_atr": NA, "average_mae_atr": NA, "whipsaw_rate_percent": NA,
            "walk_forward_status": NA, "blind_forward_status": NA,
            "eligibility": "RESEARCH_ONLY_NOT_ELIGIBLE_FOR_PROFILE_ASSIGNMENT",
            "reason": f"Candidate frequency only; mean confidence {_mean(data['confidence'], samples)} is not performance.",
            "source_dataset": "automatic/schema_v2/candidates.jsonl",
        })
    tier = {"C_OBSERVATIONAL_FORWARD_EXCURSION": 0, "D_CANDIDATE_ONLY": 1}
    rows.sort(key=lambda r: (tier.get(r["evidence_tier"], 9), -int(r["samples"]), r["pattern"], r["timeframe"]))
    for index, row in enumerate(rows, 1): row["evidence_order"] = index
    return {
        "schema": "afip.a30.research_decision_matrix.v1", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "MATRIX_GENERATED", "rows": rows, "row_count": len(rows),
        "observational_rows": sum(r["evidence_tier"].startswith("C_") for r in rows),
        "candidate_only_rows": sum(r["evidence_tier"].startswith("D_") for r in rows),
        "closed_trade_performance_rows": 0,
        "ranking_method": "Evidence tier, then exact-segment sample size; no synthetic performance score.",
        "profile_strategy_selection": "NOT_DECIDED", "automatic_profile_assignment": False,
        "automatic_research_promotion": False, "execution_authority": "NONE", "orders_sent": False,
        "truth_notice": "Win rate, expectancy, profit factor and drawdown remain DATA_UNAVAILABLE until exact-segment closed-position outcomes exist.",
    }


def main(argv: Iterable[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True); parser.add_argument("--output")
    args = parser.parse_args(argv); root = Path(args.project_root).resolve()
    output = Path(args.output).resolve() if args.output else root / "runtime/research/a30_research_decision_matrix.json"
    report = build_report(root); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "row_count", "observational_rows", "candidate_only_rows", "closed_trade_performance_rows", "profile_strategy_selection", "execution_authority")}, indent=2))
    print(f"A30 report: {output}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
