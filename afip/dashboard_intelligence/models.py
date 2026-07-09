"""Dashboard intelligence integration models for Production Milestone H Pack 9.

This layer aggregates existing deterministic runtime reports for display. It is
presentation/readiness only and never changes trading decisions or enables live
execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DashboardEngineRow:
    english_name: str
    thai_name: str
    description: str
    input: str
    output: str
    status_icon: str
    status: str
    confidence: float
    accuracy: float
    win_rate: float
    runtime: str
    waiting_reason: str
    dependency: str
    health: str
    research_statistics: str
    live_statistics: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DashboardDecisionExplanation:
    waiting_reason: str
    entry_reason: str
    holding_reason: str
    stop_loss_reason: str
    break_even_reason: str
    trailing_reason: str
    partial_close_reason: str
    exit_reason: str
    rejected_entry_reason: str
    rejected_exit_reason: str
    alternative_decision: str
    current_ai_reasoning: str
    expected_next_action: str
    risk_status: str
    estimated_next_review: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DashboardIntelligenceReport:
    status: str
    reason: str
    broker: str
    symbol: str
    profile_name: str
    mode: str
    runtime_status: str
    profile_status: str
    research_center_status: str
    paper_trading_status: str
    afip_bank_status: str
    historical_data_status: str
    market_status: str
    engine_rows: tuple[DashboardEngineRow, ...]
    decision_explanation: DashboardDecisionExplanation
    research_statistics_scope: str
    live_statistics_scope: str
    order_center_statuses: tuple[str, ...]
    dashboard_sections: tuple[str, ...]
    validation_items: tuple[str, ...]
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["engine_rows"] = [row.as_dict() for row in self.engine_rows]
        data["decision_explanation"] = self.decision_explanation.as_dict()
        return data
