"""Connection Manager report objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ConnectionManagerReport:
    status: str
    reason: str
    connection_gate: str
    internet_status: str
    internet_disconnect_count: int
    internet_disconnect_duration_seconds: int
    reconnect_count: int
    mt5_status: str
    broker_status: str
    market_status: str
    trading_session: str
    profile_name: str
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    runtime_seconds: int
    waiting_reason: str
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_text(self) -> str:
        return (
            "AFIP Connection Manager\n"
            f"Status: {self.status}\n"
            f"Gate: {self.connection_gate}\n"
            f"Reason: {self.reason}\n"
            f"Internet: {self.internet_status}\n"
            f"MT5: {self.mt5_status}\n"
            f"Broker: {self.broker_status}\n"
            f"Market: {self.market_status}\n"
            f"Session: {self.trading_session}\n"
            f"Waiting Reason: {self.waiting_reason}"
        )
