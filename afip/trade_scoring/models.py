from dataclasses import dataclass


@dataclass(frozen=True)
class TradeScore:
    opportunity_id: str
    symbol: str
    direction: str
    opportunity_score: float
    quality_score: float
    risk_adjusted_score: float
    execution_readiness_score: float
    final_score: float
    grade: str
    eligible: bool
    explanation_en: str
    explanation_th: str


@dataclass(frozen=True)
class TradeScoringReport:
    status: str
    reason: str
    scores: tuple[TradeScore, ...]
    top_opportunity_id: str
    top_direction: str
    top_final_score: float
    top_grade: str
    eligible_count: int
    score_count: int
    expected_next_action_en: str
    expected_next_action_th: str
    next_review_time_utc: str
    direct_execution: bool = False
