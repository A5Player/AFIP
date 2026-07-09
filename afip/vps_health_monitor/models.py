"""VPS Health Monitor models for Production Bring-up Pack 1.

The health monitor is operational telemetry only. It does not change trading
logic, does not enable live execution, and is safe to render on the dashboard.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class VPSHealthReport:
    """Observable Windows VPS health report for dashboard runtime."""

    status: str
    reason: str
    hostname: str
    operating_system: str
    windows_version: str
    architecture: str
    python_version: str
    uptime_seconds: int
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    disk_free_gb: float
    disk_total_gb: float
    health_gate: str
    dashboard_message_th: str
    dashboard_message_en: str
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_text(self) -> str:
        return (
            "AFIP VPS Health Monitor\n"
            f"Status: {self.status}\n"
            f"Reason: {self.reason}\n"
            f"Host: {self.hostname}\n"
            f"OS: {self.operating_system}\n"
            f"CPU: {self.cpu_percent}%\n"
            f"RAM: {self.ram_percent}%\n"
            f"Disk: {self.disk_percent}%\n"
            f"Gate: {self.health_gate}"
        )
