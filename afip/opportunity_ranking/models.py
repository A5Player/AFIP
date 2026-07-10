from dataclasses import dataclass


@dataclass(frozen=True)
class OpportunityCandidate:
    opportunity_id: str
    symbol: str
    direction: str
    regime_score: float
    consensus_score: float
    structure_score: float
    timing_score: float
    risk_score: float
    cost_score: float
    total_score: float
    rank: int
    eligible: bool
    block_reason_en: str
    block_reason_th: str


@dataclass(frozen=True)
class OpportunityRankingReport:
    status: str
    reason: str
    ranked_opportunities: tuple[OpportunityCandidate, ...]
    top_opportunity_id: str
    top_direction: str
    top_score: float
    opportunity_count: int
    eligible_count: int
    expected_next_action_en: str
    expected_next_action_th: str
    next_review_time_utc: str
    direct_execution: bool = False
