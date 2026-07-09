"""Internet and broker latency telemetry models for Production Bring-up Pack 3.

This module is operational telemetry only. It performs read-only connectivity
checks and never changes trading logic or enables live execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class InternetConnectivityReport:
    """Connectivity, broker reachability, and latency report for dashboard display."""

    status: str
    reason: str
    internet_status: str
    broker_status: str
    dns_status: str
    broker_host: str
    broker_port: int
    broker_latency_ms: float
    dns_latency_ms: float
    disconnect_count: int
    reconnect_count: int
    disconnect_duration_seconds: int
    connection_gate: str
    dashboard_message_th: str
    dashboard_message_en: str
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_text(self) -> str:
        return (
            "AFIP Internet Connectivity\n"
            f"Status: {self.status}\n"
            f"Reason: {self.reason}\n"
            f"Internet: {self.internet_status}\n"
            f"Broker: {self.broker_status}\n"
            f"DNS: {self.dns_status}\n"
            f"Broker Latency: {self.broker_latency_ms} ms\n"
            f"DNS Latency: {self.dns_latency_ms} ms\n"
            f"Gate: {self.connection_gate}"
        )
