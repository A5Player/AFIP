from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from afip.advisory_integration_certification import AdvisoryIntegrationCertificationRuntime
from afip.milestone_w_closure import MilestoneWClosureRuntime


def main() -> int:
    parser = argparse.ArgumentParser(description="Close AFIP Milestone W")
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--output",
        default="runtime/control/milestone_w/milestone_w_closure.json",
    )
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    certification = AdvisoryIntegrationCertificationRuntime(root).certify()
    closure_runtime = MilestoneWClosureRuntime(root)
    closure = closure_runtime.close(asdict(certification))
    output = closure_runtime.write_atomic(closure, root / args.output)

    print(json.dumps({
        "status": closure.status,
        "reason": closure.reason,
        "closure_id": closure.closure_id,
        "certification_id": closure.certification_id,
        "completed_packs": list(closure.completed_packs),
        "output": str(output),
        "execution_authority": closure.execution_authority,
    }, indent=2, ensure_ascii=False))

    return 0 if closure.status == "MILESTONE_W_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
