"""Command line entry point for the four AFIP dashboards."""
from __future__ import annotations
import sys
from .launcher import launch_three_dashboards
from .home import HOME_FILENAME


def main()->int:
    if len(sys.argv)>1 and sys.argv[1].lower() == "--live":
        from .live_service import run_live_dashboard
        interval = int(sys.argv[2]) if len(sys.argv)>2 else 10
        run_live_dashboard(interval_seconds=interval)
        return 0
    output=sys.argv[1] if len(sys.argv)>1 else "runtime/dashboard"
    p1,p2,p3=launch_three_dashboards(output)
    print(f"AFIP Dashboard Home generated: {p1.parent / HOME_FILENAME}", flush=True)
    print(f"AFIP Dashboard 1 generated: {p1}", flush=True)
    print(f"AFIP Dashboard 2 generated: {p2}", flush=True)
    print(f"AFIP Execution Pipeline Dashboard generated: {p1.parent / 'afip_execution_pipeline_dashboard.html'}", flush=True)
    print(f"AFIP Order Evidence Dashboard generated: {p1.parent / 'afip_order_evidence_dashboard.html'}", flush=True)
    print(f"AFIP Live MT5 Dashboard generated: {p1.parent / 'afip_live_mt5_dashboard.html'}", flush=True)
    print(f"AFIP Research Observability Dashboard generated: {p1.parent / 'afip_research_observability_dashboard.html'}", flush=True)
    print(f"AFIP Dashboard Audit generated: {p1.parent / 'afip_dashboard_audit.html'}", flush=True)
    print(f"AFIP Unified Dashboard generated: {p1.parent / 'afip_unified_dashboard.html'}", flush=True)
    print(f"AFIP Dashboard Completeness generated: {p1.parent / 'afip_dashboard_completeness.html'}", flush=True)
    print(f"AFIP Dashboard 3 generated: {p3}", flush=True)
    print(f"AFIP Dashboard 4 generated: {p1.parent / 'afip_research_operations_dashboard.html'}", flush=True)
    print(f"AFIP Control Center generated: {p1.parent / 'afip_control_center.html'}", flush=True)
    print("Dashboard 1 refreshes every 5 seconds. Dashboards 2 and 3 refresh manually.", flush=True)
    print("Automatic research is not run synchronously during dashboard generation.", flush=True)
    print("Financial placeholders are disabled. Live execution authority remains unchanged.", flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())

# AFIP_V1_BOTTOM_SAFETY_CONTRACT
from afip.dashboard_bottom_safety import ensure_primary_dashboard_bottom_safety as _afip_ensure_bottom_safety
_afip_ensure_bottom_safety()
