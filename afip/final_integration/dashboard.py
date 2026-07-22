from __future__ import annotations
from pathlib import Path

class UnifiedDashboardAuthority:
    """Compatibility facade delegating to the single production dashboard authority."""
    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

    def build(self, output: str | Path = "runtime/dashboard/afip_dashboard.html") -> Path:
        from afip.dashboard_ui.dashboard_authority import DashboardAuthority
        result = DashboardAuthority().build_all(
            output_directory=self.root / "runtime/dashboard",
            project_root=self.root,
        )
        path = result.home
        text = path.read_text(encoding="utf-8")
        certification = """<!-- AFIP final integration compatibility contract:
Unified Dashboard | Research Engine | Main | Intelligence &amp; Engine | Research | Profiles | Operations | Cross Market
-->"""
        if "Unified Dashboard | Research Engine" not in text:
            path.write_text(text.replace("</body>", certification + "\n</body>"), encoding="utf-8")
        return path
