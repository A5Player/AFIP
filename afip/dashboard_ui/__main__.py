"""Command line entry point for the AFIP visible dashboard."""

from __future__ import annotations

import sys

from .launcher import launch_dashboard


def main() -> int:
    output = sys.argv[1] if len(sys.argv) > 1 else "runtime/dashboard/afip_dashboard.html"
    path = launch_dashboard(output)
    print(f"AFIP Dashboard UI generated: {path}")
    print("Live execution remains disabled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
