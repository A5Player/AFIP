from dataclasses import dataclass

@dataclass(frozen=True)
class ConflictItem:
    source: str
    direction: str
    weighted_score: float
    severity: str

@dataclass(frozen=True)
class ConflictResolutionReport:
    status: str
    original_consensus: str
    resolved_consensus: str
    conflict_level: str
    conflict_score: float
    resolution_method: str
    unresolved_sources: tuple[str, ...]
    resolved_sources: tuple[str, ...]
    waiting_reason_en: str
    waiting_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    next_review_time_utc: str
    direct_execution: bool = False
