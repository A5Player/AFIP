"""MT5 live account telemetry models for Production Bring-up Pack 2.

This module is read-only operational telemetry. It does not send orders,
does not enable live execution, and only exposes account, broker, symbol, and
tick values for the dashboard.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MT5LiveAccountReport:
    """Read-only MT5 account and broker status for dashboard display."""

    status: str
    reason: str
    broker: str
    symbol: str
    server: str
    login: str
    account_name: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    leverage: str
    currency: str
    tick_available: bool
    bid: float
    ask: float
    spread_points: float
    point: float
    digits: str
    last_tick_time: str
    account_gate: str
    dashboard_message_th: str
    dashboard_message_en: str
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_text(self) -> str:
        return (
            "AFIP MT5 Live Account\n"
            f"Status: {self.status}\n"
            f"Reason: {self.reason}\n"
            f"Broker: {self.broker}\n"
            f"Server: {self.server}\n"
            f"Login: {self.login}\n"
            f"Symbol: {self.symbol}\n"
            f"Balance: {self.balance}\n"
            f"Equity: {self.equity}\n"
            f"Spread: {self.spread_points}\n"
            f"Gate: {self.account_gate}"
        )
