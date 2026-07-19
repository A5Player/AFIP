"""Dashboard UI launcher with data-integrity-safe defaults."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from .runtime import DashboardUIRuntime
from .split_runtime import ThreeDashboardRuntime, TwoDashboardRuntime
from .home import write_dashboard_home
from .cross_market import write_cross_market_dashboard
from afip.automatic_research_runtime import AutomaticResearchRuntime


def default_dashboard_record() -> dict[str, Any]:
    """Return configuration context only; never invent account or financial values."""
    return {
        "broker":"XM","symbol":"GOLD#","mode":"DEMO",
        "four_profile_config_path":"config/four_profile_demo.json",
        "execution_mode":"DEMO","research_center_requested":True,
        "financial_data_policy":"REAL_SOURCE_ONLY",
        "placeholder_financial_data":False,
    }


def launch_dashboard(output_path: str | Path="runtime/dashboard/afip_dashboard.html",record:dict[str,Any]|None=None)->Path:
    """Backward-compatible legacy renderer API."""
    return DashboardUIRuntime().write_html(record or default_dashboard_record(),output_path)


def launch_two_dashboards(output_directory:str|Path="runtime/dashboard",record:dict[str,Any]|None=None)->tuple[Path,Path]:
    return TwoDashboardRuntime().write_dashboards(record or default_dashboard_record(),output_directory)


def _research_bootstrap_requested(explicit: bool | None) -> bool:
    if explicit is not None:
        return explicit
    value = os.environ.get("AFIP_DASHBOARD_RUN_RESEARCH", "").strip().upper()
    return value in {"1", "TRUE", "YES", "ON"}


def launch_three_dashboards(
    output_directory:str|Path="runtime/dashboard",
    record:dict[str,Any]|None=None,
    project_root:str|Path=".",
    *,
    run_research_bootstrap: bool | None = None,
)->tuple[Path,Path,Path]:
    """Generate all three dashboards and the dashboard home page.

    Automatic historical research is intentionally not executed synchronously by
    default. Dashboard generation must remain fast, deterministic and read-only.
    Set ``run_research_bootstrap=True`` or ``AFIP_DASHBOARD_RUN_RESEARCH=YES``
    only when an operator intentionally wants research collection before render.
    """
    if _research_bootstrap_requested(run_research_bootstrap):
        AutomaticResearchRuntime(project_root).run()
    paths = ThreeDashboardRuntime().write_three_dashboards(
        record or default_dashboard_record(), output_directory, project_root
    )
    write_cross_market_dashboard(output_directory, project_root)
    write_dashboard_home(output_directory)
    return paths
