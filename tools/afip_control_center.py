"""Read-only AFIP V1 Control Center command line utility."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from afip.control_center_runtime import ControlCenterRuntime
from afip.dashboard_ui.control_center import write_control_center


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect or build the passive AFIP V1 Control Center.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--snapshot", action="store_true", help="Print the current read-only runtime projection as JSON.")
    parser.add_argument("--build", action="store_true", help="Build runtime/dashboard/afip_control_center.html.")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if args.snapshot or not args.build:
        print(json.dumps(ControlCenterRuntime(root).snapshot(), ensure_ascii=False, indent=2, sort_keys=True))
    if args.build:
        print(write_control_center(root / "runtime" / "dashboard", root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
