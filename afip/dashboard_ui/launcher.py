"""Dashboard UI launcher with data-integrity-safe defaults."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from .runtime import DashboardUIRuntime
from .split_runtime import ThreeDashboardRuntime, TwoDashboardRuntime
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
    return DashboardUIRuntime().write_html(record or default_dashboard_record(),output_path)


def launch_two_dashboards(output_directory:str|Path="runtime/dashboard",record:dict[str,Any]|None=None)->tuple[Path,Path]:
    return TwoDashboardRuntime().write_dashboards(record or default_dashboard_record(),output_directory)


def launch_three_dashboards(output_directory:str|Path="runtime/dashboard",record:dict[str,Any]|None=None,project_root:str|Path=".")->tuple[Path,Path,Path]:
    # Every AFIP dashboard start performs a safe incremental research bootstrap.
    # Failures remain visible in automatic_research_status.json and never grant execution authority.
    AutomaticResearchRuntime(project_root).run()
    return ThreeDashboardRuntime().write_three_dashboards(record or default_dashboard_record(),output_directory,project_root)
