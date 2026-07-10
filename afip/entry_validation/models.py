from dataclasses import dataclass


@dataclass(frozen=True)
class EntryValidation:
    opportunity_id: str
    symbol: str
    direction: str
    allocated_units: int
    lot_per_unit: float
    total_lot: float
    market_regime_ready: bool
    conflict_allowed: bool
    trade_score_allowed: bool
    risk_allowed: bool
    timing_allowed: bool
    spread_allowed: bool
    allocation_allowed: bool
    approved: bool
    block_reasons: tuple[str, ...]
    explanation_en: str
    explanation_th: str


@dataclass(frozen=True)
class EntryValidationReport:
    status: str
    reason: str
    validations: tuple[EntryValidation, ...]
    selected_opportunity_id: str
    selected_direction: str
    approved_units: int
    lot_per_unit: float
    total_lot: float
    entry_approved: bool
    waiting_reason_en: str
    waiting_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    next_review_time_utc: str
    direct_execution: bool = False
