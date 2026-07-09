"""Research Center models for AFIP Milestone H Pack 6.

Research Center separates research statistics from live statistics. It provides
ranked analytical summaries for dashboard and future walk-forward workflows
without enabling live execution or changing trading decisions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ResearchMetricRow:
    rank: int
    category: str
    name: str
    sample_size: int
    win_rate: float
    profit_factor: float
    expectancy: float
    drawdown: float
    risk_score: float
    score: float
    thai_description: str
    english_description: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchStatisticGroup:
    name: str
    thai_name: str
    english_description: str
    statistic_scope: str
    rows: tuple[ResearchMetricRow, ...]

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["rows"] = [row.as_dict() for row in self.rows]
        return data


@dataclass(frozen=True)
class ResearchCenterReport:
    status: str
    reason: str
    profile_name: str
    profile_type: str
    broker: str
    symbol: str
    research_scope: str
    live_scope: str
    minimum_orders_required: int
    completed_research_orders: int
    research_ready: bool
    walk_forward_ready: bool
    standard_learning_candidate: bool
    standard_learning_policy: str
    top_trading_hours: ResearchStatisticGroup
    top_trading_sessions: ResearchStatisticGroup
    top_market_regimes: ResearchStatisticGroup
    top_entry_plans: ResearchStatisticGroup
    top_exit_plans: ResearchStatisticGroup
    top_patterns: ResearchStatisticGroup
    top_engine_combinations: ResearchStatisticGroup
    top_profit_reasons: ResearchStatisticGroup
    top_loss_reasons: ResearchStatisticGroup
    dashboard_sections: tuple[str, ...]
    validation_items: tuple[str, ...]
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in (
            "top_trading_hours",
            "top_trading_sessions",
            "top_market_regimes",
            "top_entry_plans",
            "top_exit_plans",
            "top_patterns",
            "top_engine_combinations",
            "top_profit_reasons",
            "top_loss_reasons",
        ):
            data[key] = getattr(self, key).as_dict()
        return data

    def as_text(self) -> str:
        return (
            "AFIP Research Center\n"
            f"Status: {self.status}\n"
            f"Reason: {self.reason}\n"
            f"Profile: {self.profile_name}\n"
            f"Broker: {self.broker}\n"
            f"Symbol: {self.symbol}\n"
            f"Research Scope: {self.research_scope}\n"
            f"Live Scope: {self.live_scope}\n"
            f"Completed Research Orders: {self.completed_research_orders}\n"
            f"Standard Learning Candidate: {self.standard_learning_candidate}"
        )
