"""Command line entry point for the three AFIP dashboards."""
from __future__ import annotations
import sys
from .launcher import launch_three_dashboards

def main()->int:
    output=sys.argv[1] if len(sys.argv)>1 else "runtime/dashboard"
    p1,p2,p3=launch_three_dashboards(output)
    print(f"AFIP Dashboard 1 generated: {p1}")
    print(f"AFIP Dashboard 2 generated: {p2}")
    print(f"AFIP Dashboard 3 generated: {p3}")
    print("Dashboard 1 refreshes every 5 seconds. Dashboards 2 and 3 refresh manually.")
    print("Financial placeholders are disabled. Live execution authority remains unchanged.")
    return 0
if __name__=="__main__": raise SystemExit(main())
