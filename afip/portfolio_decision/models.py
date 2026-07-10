from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioDecision:
    portfolio_id: str
    symbol: str
    current_units: int
    maximum_units: int
    available_units: int
    entry_units: int
    exit_units: int
    decision: str
    direction: str
    risk_allowed: bool
    exposure_allowed: bool
    entry_allowed: bool
    position_action_allowed: bool
    approved: bool
    block_reasons: tuple[str, ...]
    explanation_en: str
    explanation_th: str


@dataclass(frozen=True)
class PortfolioDecisionReport:
    status: str
    reason: str
    decisions: tuple[PortfolioDecision, ...]
    selected_portfolio_id: str
    portfolio_decision: str
    selected_direction: str
    approved_units: int
    current_units: int
    maximum_units: int
    available_units: int
    portfolio_risk_status: str
    waiting_reason_en: str
    waiting_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    next_review_time_utc: str
    direct_execution: bool = False
