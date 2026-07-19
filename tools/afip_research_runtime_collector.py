"""Collect AFIP runtime ledgers into the research dataset without trading side effects."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from afip.four_profile_operations.runtime import FourProfileOperationalRuntime
from afip.research_data_foundation import ResearchRuntimeCollector


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/four_profile_demo.json")
    parser.add_argument("--output", default="runtime/research")
    args = parser.parse_args()
    profiles = FourProfileOperationalRuntime(Path(args.config)).load()
    ledgers = [profile.logs_directory / "demo_execution_ledger.jsonl" for profile in profiles if profile.enabled and profile.research_enabled]
    report = ResearchRuntimeCollector(Path(args.output)).ingest_ledgers(ledgers)
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
