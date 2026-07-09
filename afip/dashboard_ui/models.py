"""Dashboard UI models for Production Milestone H Pack 8.

The dashboard UI layer is presentation only. It reads deterministic runtime
reports from existing managers and renders an observable dashboard document
without changing trading logic or enabling live execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DashboardPanel:
    panel_id: str
    title_en: str
    title_th: str
    status: str
    description_en: str
    description_th: str
    rows: tuple[tuple[str, str], ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DashboardUIReport:
    status: str
    reason: str
    page_title: str
    profile_name: str
    broker: str
    symbol: str
    mode: str
    live_execution_enabled: bool
    panels: tuple[DashboardPanel, ...]
    navigation_sections: tuple[str, ...]
    visible_dashboard_ready: bool
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["panels"] = [panel.as_dict() for panel in self.panels]
        return data

    def as_text(self) -> str:
        lines = [
            self.page_title,
            f"Status: {self.status}",
            f"Reason: {self.reason}",
            f"Profile: {self.profile_name}",
            f"Broker: {self.broker}",
            f"Symbol: {self.symbol}",
            f"Mode: {self.mode}",
            f"Live Execution: {self.live_execution_enabled}",
        ]
        for panel in self.panels:
            lines.append(f"[{panel.status}] {panel.title_en} / {panel.title_th}")
            for key, value in panel.rows:
                lines.append(f" - {key}: {value}")
        return "\n".join(lines)
