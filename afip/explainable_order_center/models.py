"""Explainable Order Center models for Production Bring-up Pack 5.

This module is read-only. It converts existing paper order and decision fields
into bilingual dashboard explanations. It does not send broker orders and does
not enable live execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BilingualExplanation:
    """English and Thai explanation for one observable decision field."""

    key: str
    title_en: str
    title_th: str
    value: str
    explanation_en: str
    explanation_th: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExplainableOrderItem:
    """One order explanation row for the dashboard."""

    order_id: str
    symbol: str
    side: str
    status: str
    units: int
    lot_per_unit: float
    total_lot: float
    confidence: float
    risk_status: str
    expected_next_action: str
    next_review_time: str
    explanations: tuple[BilingualExplanation, ...]

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["explanations"] = [item.as_dict() for item in self.explanations]
        return data


@dataclass(frozen=True)
class ExplainableOrderCenterReport:
    """Dashboard-ready explainable order center report."""

    status: str
    reason: str
    broker: str
    symbol: str
    live_execution_enabled: bool
    order_count: int
    visible_explanation_fields: tuple[str, ...]
    orders: tuple[ExplainableOrderItem, ...]
    dashboard_ready: bool
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["orders"] = [order.as_dict() for order in self.orders]
        return data
