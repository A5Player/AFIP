from __future__ import annotations

import argparse
import json
from pathlib import Path

from afip.production_certification import ProductionCertificationRuntime
from afip.production_certification.incremental_financial_naming import (
    run_incremental_financial_naming,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP V1 Production Certification")
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)

    certify = sub.add_parser("certify")
    certify.add_argument("--full-regression", action="store_true")
    certify.add_argument("--force-financial-naming", action="store_true")
    certify.add_argument("--mt5-check", action="store_true")

    naming = sub.add_parser("financial-naming")
    naming.add_argument("--force", action="store_true")
    naming.add_argument("--timeout-seconds", type=int, default=180)

    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "financial-naming":
        result = run_incremental_financial_naming(
            root,
            force=args.force,
            timeout_seconds=args.timeout_seconds,
        )
    else:
        result = ProductionCertificationRuntime(root).certify(
            full_regression=args.full_regression,
            force_financial_naming=args.force_financial_naming,
            mt5_check=args.mt5_check,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"PASS", "READY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
