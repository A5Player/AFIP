"""Command line entry point for the four AFIP dashboards."""
from __future__ import annotations
import sys
from .launcher import launch_three_dashboards
from .home import HOME_FILENAME


def main()->int:
    output=sys.argv[1] if len(sys.argv)>1 else "runtime/dashboard"
    p1,p2,p3=launch_three_dashboards(output)
    print(f"AFIP Dashboard Home generated: {p1.parent / HOME_FILENAME}", flush=True)
    print(f"AFIP Dashboard 1 generated: {p1}", flush=True)
    print(f"AFIP Dashboard 2 generated: {p2}", flush=True)
    print(f"AFIP Dashboard 3 generated: {p3}", flush=True)
    print(f"AFIP Dashboard 4 generated: {p1.parent / 'afip_research_operations_dashboard.html'}", flush=True)
    print("Dashboard 1 refreshes every 5 seconds. Dashboards 2 and 3 refresh manually.", flush=True)
    print("Automatic research is not run synchronously during dashboard generation.", flush=True)
    print("Financial placeholders are disabled. Live execution authority remains unchanged.", flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
