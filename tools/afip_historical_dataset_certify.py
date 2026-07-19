from __future__ import annotations
import argparse, csv, json
from pathlib import Path
from typing import Any, Iterable
from afip.historical_dataset_certification import HistoricalDatasetCertifier, write_report


def rows(path: Path) -> Iterable[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    yield value
    elif path.suffix.lower() == ".json":
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        source = value if isinstance(value, list) else value.get("records", [])
        for item in source:
            if isinstance(item, dict):
                yield item
    elif path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            yield from csv.DictReader(stream)
    else:
        raise ValueError(f"unsupported input format: {path.suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Certify historical OHLC dataset readiness for AFIP research.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--instrument", default="GOLD#")
    parser.add_argument("--source-id", default="VPS_HISTORICAL_DATA")
    parser.add_argument("--policy", default="config/historical_dataset_certification/readiness_policy.json")
    parser.add_argument("--output", default="runtime/research/certification/historical_dataset_readiness.json")
    args = parser.parse_args()
    certifier = HistoricalDatasetCertifier.from_policy_file(args.policy)
    report = certifier.certify(rows(Path(args.input)), instrument=args.instrument, source_id=args.source_id)
    write_report(report, args.output)
    print(f"Historical Dataset Certification: {report.overall_status}")
    print(f"Research eligible: {report.research_eligible}")
    for item in report.timeframe_results:
        print(f"{item.timeframe}: {item.status} records={item.valid_records} missing={item.estimated_missing_records} quality={item.quality_score}")
    print(f"Report: {args.output}")
    return 0 if report.overall_status != "QUARANTINED" else 2

if __name__ == "__main__":
    raise SystemExit(main())
