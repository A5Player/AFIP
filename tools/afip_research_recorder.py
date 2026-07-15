from __future__ import annotations

import argparse
import json
from pathlib import Path

from afip.research_data_foundation import ResearchRecorder


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="AFIP read-only research ledger recorder")
    sub = p.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest-ledger", help="Ingest one demo execution JSONL ledger")
    ingest.add_argument("ledger", type=Path)
    ingest.add_argument("--output", type=Path, default=Path("runtime/research"))
    status = sub.add_parser("status", help="Show current research index")
    status.add_argument("--output", type=Path, default=Path("runtime/research"))
    return p


def main() -> int:
    args = parser().parse_args()
    if args.command == "ingest-ledger":
        summary = ResearchRecorder(args.output).ingest_ledger(args.ledger)
        print(json.dumps(summary.as_dict(), indent=2, sort_keys=True))
        return 0
    index = args.output / "research_index.json"
    if not index.exists():
        print(json.dumps({"status": "WAITING", "reason": "research_index_not_created"}, indent=2))
        return 0
    print(index.read_text(encoding="utf-8-sig"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
