"""Read-only AFIP Bank models for Production Bring-up Pack 6."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True)
class BankTransaction:
    transaction_id: str
    transaction_type: str
    amount: float
    currency: str
    occurred_at: str
    reference: str
    note_en: str
    note_th: str
    def as_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class AFIPBankReport:
    status: str
    reason: str
    broker: str
    symbol: str
    mode: str
    currency: str
    initial_capital: float
    deposits: float
    withdrawals: float
    closed_profit: float
    floating_profit: float
    balance: float
    equity: float
    reserve: float
    available_allocation: float
    lifetime_return_percent: float
    transaction_count: int
    transactions: tuple[BankTransaction, ...]
    dashboard_explanation_en: str
    dashboard_explanation_th: str
    validation_items: tuple[str, ...]
    live_execution_enabled: bool = False
    trading_logic_changed: bool = False
    def as_dict(self) -> dict[str, Any]:
        data = asdict(self); data["transactions"] = [x.as_dict() for x in self.transactions]; return data
