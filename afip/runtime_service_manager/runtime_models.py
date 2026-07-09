"""Runtime Service Manager models for Windows VPS operation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RuntimeEvent:
    """Single observable runtime event for dashboard timeline."""

    sequence: int
    event_name: str
    status: str
    reason: str
    action: str
    dashboard_message_th: str
    dashboard_message_en: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeServiceReport:
    """Runtime service readiness report."""

    status: str
    reason: str
    runtime_gate: str
    supervisor_status: str
    heartbeat_status: str
    recovery_status: str
    internet_status: str
    mt5_status: str
    broker_status: str
    trading_status: str
    waiting_reason: str
    expected_next_action: str
    runtime_seconds: int
    heartbeat_age_seconds: int
    restart_count: int
    unexpected_exception_count: int
    reconnect_count: int
    internet_disconnect_count: int
    internet_disconnect_duration_seconds: int
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    event_history: tuple[RuntimeEvent, ...]
    dashboard_sections: tuple[str, ...]
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["event_history"] = [event.as_dict() for event in self.event_history]
        return data

    def as_text(self) -> str:
        return (
            "AFIP Runtime Service Manager\n"
            f"Status: {self.status}\n"
            f"Gate: {self.runtime_gate}\n"
            f"Reason: {self.reason}\n"
            f"Supervisor: {self.supervisor_status}\n"
            f"Heartbeat: {self.heartbeat_status}\n"
            f"Recovery: {self.recovery_status}\n"
            f"Trading: {self.trading_status}\n"
            f"Waiting Reason: {self.waiting_reason}\n"
            f"Expected Next Action: {self.expected_next_action}"
        )
