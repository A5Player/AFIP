"""Single production authority for every AFIP dashboard build entry point."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

HOME_FILENAME = "afip_dashboard.html"
PROFILE_FILENAME = "afip_profiles_dashboard.html"
INTELLIGENCE_FILENAME = "afip_intelligence_engine_dashboard.html"
RESEARCH_FILENAME = "afip_research_data_dashboard.html"
OPERATIONS_FILENAME = "afip_research_operations_dashboard.html"
CROSS_MARKET_FILENAME = "afip_cross_market_intelligence_dashboard.html"
CONTROL_CENTER_FILENAME = "afip_control_center.html"
POLICY_VERSION = "AFIP_V1_SINGLE_DASHBOARD_AUTHORITY_V2"


@dataclass(frozen=True)
class DashboardBuildResult:
    output_directory: Path
    home: Path
    profiles: Path
    intelligence: Path
    research: Path
    research_operations: Path
    cross_market: Path
    control_center: Path
    profile_details: tuple[Path, ...] = ()
    policy_version: str = POLICY_VERSION


def _atomic_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)
    return path


class DashboardAuthority:
    """Only authority allowed to coordinate AFIP dashboard output."""

    def build_all(
        self,
        output_directory: str | Path = "runtime/dashboard",
        record: Mapping[str, Any] | None = None,
        project_root: str | Path = ".",
    ) -> DashboardBuildResult:
        from .split_runtime import LIVE_STATUS_FILENAME, ThreeDashboardRuntime
        from .home import render_dashboard_home
        from .cross_market import render_cross_market_dashboard
        from .research_operations import render_research_operations
        from .launcher import default_dashboard_record
        from .control_center import PROFILE_DETAIL_FILENAMES, render_control_center, render_profile_detail

        directory = Path(output_directory)
        directory.mkdir(parents=True, exist_ok=True)
        from afip.dashboard_data_contract import build_dashboard_contract
        contract = build_dashboard_contract(project_root)
        renderer = ThreeDashboardRuntime()
        data = dict(record or default_dashboard_record())
        data["dashboard_data_contract"] = contract
        data["profiles"] = contract.get("profiles", [])
        data["project_root"] = str(project_root)
        p1 = _atomic_text(directory / PROFILE_FILENAME, renderer.render_profiles_html(data))
        p2 = _atomic_text(directory / INTELLIGENCE_FILENAME, renderer.render_intelligence_html(data))
        p3 = _atomic_text(directory / RESEARCH_FILENAME, renderer.render_research_html(data, project_root))
        # Keep the lightweight dashboard build contract compatible with legacy
        # renderers used by integrations/tests.  The production renderer owns
        # the live-status panel; a deliberately minimal renderer can still
        # refresh the established three priority pages without gaining any new
        # responsibility or authority.
        render_live_status = getattr(renderer, "render_live_status_html", None)
        if callable(render_live_status):
            _atomic_text(directory / LIVE_STATUS_FILENAME, render_live_status(data, project_root))
        cross = _atomic_text(directory / CROSS_MARKET_FILENAME, render_cross_market_dashboard(project_root))
        operations = _atomic_text(directory / OPERATIONS_FILENAME, render_research_operations(project_root))
        control = _atomic_text(directory / CONTROL_CENTER_FILENAME, render_control_center(project_root))
        details = tuple(
            _atomic_text(directory / filename, render_profile_detail(project_root, profile_id))
            for profile_id, filename in PROFILE_DETAIL_FILENAMES.items()
        )
        home = _atomic_text(directory / HOME_FILENAME, render_dashboard_home())
        return DashboardBuildResult(directory, home, p1, p2, p3, operations, cross, control, details)

    def build_live(
        self,
        output_directory: str | Path = "runtime/dashboard",
        record: Mapping[str, Any] | None = None,
        project_root: str | Path = ".",
    ) -> dict[str, Path]:
        """Refresh only lightweight operational pages.

        This runs in a separate background process.  It reads existing JSON
        evidence only and has no MT5 or order authority.
        """
        from .split_runtime import LIVE_STATUS_FILENAME, ThreeDashboardRuntime
        from .home import render_dashboard_home
        from .research_operations import render_research_operations
        from .launcher import default_dashboard_record

        directory = Path(output_directory)
        directory.mkdir(parents=True, exist_ok=True)
        renderer = ThreeDashboardRuntime()
        data = dict(record or default_dashboard_record())
        from afip.dashboard_data_contract import build_dashboard_contract
        contract = build_dashboard_contract(project_root)
        data["dashboard_data_contract"] = contract
        data["profiles"] = contract.get("profiles", [])
        data["project_root"] = str(project_root)
        # The production renderer publishes the independently refreshed,
        # read-only status document.  Keep this established lightweight-build
        # contract compatible with minimal renderers used by integrations.
        render_live_status = getattr(renderer, "render_live_status_html", None)
        if callable(render_live_status):
            _atomic_text(directory / LIVE_STATUS_FILENAME, render_live_status(data, project_root))
        result = {
            # Fast pages: home, research and data-loading/operations are refreshed
            # every fast cycle.  These renderers read existing JSON evidence only.
            "home": _atomic_text(directory / HOME_FILENAME, render_dashboard_home()),
            "research": _atomic_text(directory / RESEARCH_FILENAME, renderer.render_research_html(data, project_root)),
            "research_operations": _atomic_text(directory / OPERATIONS_FILENAME, render_research_operations(project_root)),
        }
        return result
