"""A29 read-only coverage audit for every registered AFIP research dataset."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime
from afip.historical_replay_research import AppendOnlyResearchDataset

_OUTCOME_FIELDS = {"outcome", "result", "trade_result", "realized_r", "net_realized_r", "realized_profit"}
_RANK_FIELDS = {"research_rank", "rank", "overall_rank", "eligible_rank"}


def _read_records(path: Path) -> tuple[list[dict[str, Any]], bool, str]:
    if not path.exists():
        return [], True, "NOT_RECORDED"
    records: list[dict[str, Any]] = []
    chained = True
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            value = json.loads(line)
            if isinstance(value, Mapping) and isinstance(value.get("record"), Mapping):
                records.append(dict(value["record"]))
                chained = chained and bool(value.get("chain_checksum"))
            elif isinstance(value, Mapping):
                records.append(dict(value))
                chained = False
        return records, chained, "READABLE"
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return [], False, f"UNREADABLE:{type(exc).__name__}"


def _source_references(project_root: Path, dataset: str) -> tuple[list[str], list[str]]:
    producers: list[str] = []
    consumers: list[str] = []
    escaped = re.escape(dataset)
    append_pattern = re.compile(rf"\.append\(\s*['\"]{escaped}['\"]")
    consume_pattern = re.compile(rf"\.(?:records|count|verify|path_for)\(\s*['\"]{escaped}['\"]")
    registry = project_root / "afip" / "historical_replay_research" / "runtime.py"
    for path in (project_root / "afip").rglob("*.py"):
        if path == registry:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        relative = str(path.relative_to(project_root)).replace("\\", "/")
        if append_pattern.search(text):
            producers.append(relative)
        if consume_pattern.search(text) or f"{dataset}.jsonl" in text:
            consumers.append(relative)
    return sorted(set(producers)), sorted(set(consumers))


def build_report(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    research_root = root / "runtime" / "research"
    dashboard_source = (root / "afip" / "dashboard_ui" / "split_runtime.py").read_text(encoding="utf-8")
    rows: list[dict[str, Any]] = []
    for dataset in AppendOnlyResearchDataset.DATASET_NAMES:
        records, chained, persistence = _read_records(research_root / f"{dataset}.jsonl")
        producers, consumers = _source_references(root, dataset)
        outcome_records = sum(any(record.get(key) not in (None, "") for key in _OUTCOME_FIELDS) for record in records)
        ranked_records = sum(any(record.get(key) not in (None, "") for key in _RANK_FIELDS) for record in records)
        if records and producers:
            state = "EVIDENCE_RECORDED"
        elif records:
            state = "EVIDENCE_WITHOUT_STATIC_PRODUCER_REFERENCE"
        elif producers:
            state = "CODE_READY_NO_EVIDENCE"
        else:
            state = "REGISTRY_ONLY_OR_DYNAMIC_PRODUCER"
        rows.append({
            "dataset": dataset,
            "category": ThreeDashboardRuntime._research_category(dataset),
            "state": state,
            "record_count": len(records),
            "outcome_record_count": outcome_records,
            "ranked_record_count": ranked_records,
            "persistence_status": persistence,
            "append_only_chain_observed": bool(records) and chained,
            "producer_connected": bool(producers),
            "producer_files": producers,
            "consumer_connected": bool(consumers),
            "consumer_files": consumers,
            "specialized_dashboard_connected": f"{dataset}.jsonl" in dashboard_source,
            "inventory_dashboard_connected": True,
            "execution_authority": "NONE",
            "automatic_promotion_allowed": False,
        })
    categories: dict[str, dict[str, Any]] = {}
    for row in rows:
        item = categories.setdefault(row["category"], {
            "category": row["category"], "datasets": 0, "records": 0,
            "outcome_records": 0, "ranked_records": 0, "with_producer": 0,
            "with_evidence": 0, "specialized_dashboard": 0,
        })
        item["datasets"] += 1
        item["records"] += row["record_count"]
        item["outcome_records"] += row["outcome_record_count"]
        item["ranked_records"] += row["ranked_record_count"]
        item["with_producer"] += int(row["producer_connected"])
        item["with_evidence"] += int(row["record_count"] > 0)
        item["specialized_dashboard"] += int(row["specialized_dashboard_connected"])
    return {
        "schema": "afip.a29.research_pipeline_coverage.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "AUDIT_COMPLETE",
        "research_root": str(research_root),
        "registered_datasets": len(rows),
        "datasets_with_static_producer": sum(row["producer_connected"] for row in rows),
        "datasets_with_evidence": sum(row["record_count"] > 0 for row in rows),
        "datasets_with_outcomes": sum(row["outcome_record_count"] > 0 for row in rows),
        "datasets_with_rankings": sum(row["ranked_record_count"] > 0 for row in rows),
        "categories": sorted(categories.values(), key=lambda item: item["category"]),
        "datasets": rows,
        "research_only": True,
        "read_only_audit": True,
        "execution_authority": "NONE",
        "automatic_promotion_allowed": False,
        "orders_sent": False,
    }


def main(argv: Iterable[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    root = Path(args.project_root).resolve()
    output = Path(args.output).resolve() if args.output else root / "runtime" / "research" / "a29_research_pipeline_coverage.json"
    try:
        report = build_report(root)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as exc:
        print(json.dumps({"status": "AUDIT_FAILED", "reason": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    print(json.dumps({key: report[key] for key in (
        "status", "registered_datasets", "datasets_with_static_producer",
        "datasets_with_evidence", "datasets_with_outcomes", "datasets_with_rankings",
        "execution_authority", "orders_sent")}, indent=2))
    print(f"A29 report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
