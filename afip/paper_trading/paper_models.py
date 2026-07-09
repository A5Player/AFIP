"""Paper Trading models for AFIP Milestone H Pack 7.

Paper trading simulates order lifecycle, units, portfolio, and AFIP Bank values
without sending broker orders. It is designed for dashboard explainability and
Version 1 safety gates.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PaperOrderState:
    state: str
    thai_description: str
    english_description: str
    reason: str
    next_expected_action: str
    confidence: float
    risk_status: str
    estimated_next_review: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PaperOrder:
    order_id: str
    symbol: str
    side: str
    units: int
    lot_per_unit: float
    total_lot: float
    status: str
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    floating_profit: float
    closed_profit: float
    quality: str
    confidence: float
    waiting_reason: str
    entry_reason: str
    holding_reason: str
    stop_loss_reason: str
    break_even_reason: str
    trailing_reason: str
    partial_close_reason: str
    exit_reason: str
    alternative_decision: str
    current_ai_reasoning: str
    expected_next_action: str
    risk_status: str
    estimated_next_review: str
    lifecycle: tuple[PaperOrderState, ...]

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["lifecycle"] = [state.as_dict() for state in self.lifecycle]
        return data


@dataclass(frozen=True)
class PaperPortfolioReport:
    status: str
    reason: str
    broker: str
    symbol: str
    profile_name: str
    mode: str
    balance: float
    equity: float
    reserve: float
    allocation: float
    roi: float
    floating_profit: float
    closed_profit: float
    current_units: int
    maximum_units: int
    unit_lot: float
    order_count: int
    waiting_count: int
    ready_count: int
    opened_count: int
    managing_count: int
    closed_count: int
    orders: tuple[PaperOrder, ...]
    dashboard_sections: tuple[str, ...]
    validation_items: tuple[str, ...]
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["orders"] = [order.as_dict() for order in self.orders]
        return data

    def as_text(self) -> str:
        return (
            "AFIP Paper Trading Engine\n"
            f"Status: {self.status}\n"
            f"Reason: {self.reason}\n"
            f"Broker: {self.broker}\n"
            f"Symbol: {self.symbol}\n"
            f"Mode: {self.mode}\n"
            f"Balance: {self.balance}\n"
            f"Equity: {self.equity}\n"
            f"Current Units: {self.current_units}\n"
            f"Orders: {self.order_count}"
        )
