from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from afip.production_certification.runtime import FinalV1ProductionCertification
from afip.runtime_truth import build_runtime_truth

FOCUSED_TESTS = [
    "tests/test_afip_runtime_truth_certification_pack_6_5.py",
    "tests/test_afip_execution_certification_pack_7.py",
    "tests/test_afip_capital_authority_certification_pack_8.py",
    "tests/test_afip_position_management_certification_pack_9.py",
    "tests/test_afip_research_intelligence_certification_pack_10.py",
    "tests/test_afip_explainable_ai_dashboard_certification_pack_11.py",
    "tests/test_afip_v1_final_production_certification_pack_12.py",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    tests = ["tests"] if args.full else [item for item in FOCUSED_TESTS if (root / item).is_file()]
    command = [sys.executable, "-m", "pytest", *tests, "-q"]
    completed = subprocess.run(command, cwd=root, check=False)
    runtime_truth = build_runtime_truth(root)
    report = FinalV1ProductionCertification(root).certify(
        regression_status="PASS" if completed.returncode == 0 else "FAIL",
        regression_scope="FULL" if args.full else "FOCUSED",
        regression_command=command,
        regression_count=0,
        runtime_truth=runtime_truth,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if completed.returncode == 0 and report["status"] != "NOT_CERTIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
