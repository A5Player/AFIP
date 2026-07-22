"""Backward-compatible AFIP financial naming validator entry point.

The original validator is preserved by the installer as:
tools/validate_financial_naming_legacy.py

This wrapper validates a filtered source mirror and caches successful runs.
Generated runtime data, dashboards, backups and virtual environments are not
rescanned as source code.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from afip.production_certification.incremental_financial_naming import (
    run_incremental_financial_naming,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args()
    result = run_incremental_financial_naming(
        Path(args.root), force=args.force, timeout_seconds=args.timeout_seconds
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
