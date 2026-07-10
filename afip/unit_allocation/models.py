from dataclasses import dataclass


@dataclass(frozen=True)
class UnitAllocation:
    opportunity_id: str
    symbol: str
    direction: str
    trade_grade: str
    trade_score: float
    profile_name: str
    capital_per_unit: float
    available_capital: float
    profile_max_units: int
    score_max_units: int
    capital_max_units: int
    allocated_units: int
    lot_per_unit: float
    total_lot: float
    eligible: bool
    explanation_en: str
    explanation_th: str


@dataclass(frozen=True)
class UnitAllocationReport:
    status: str
    reason: str
    allocations: tuple[UnitAllocation, ...]
    selected_opportunity_id: str
    selected_direction: str
    allocated_units: int
    lot_per_unit: float
    total_lot: float
    profile_name: str
    expected_next_action_en: str
    expected_next_action_th: str
    next_review_time_utc: str
    direct_execution: bool = False
