from dataclasses import dataclass
from typing import Any
@dataclass(frozen=True)
class ConsensusContribution:
    source:str; direction:str; confidence:float; weight:float; weighted_score:float; agrees:bool
@dataclass(frozen=True)
class ConsensusReport:
    status:str; consensus:str; consensus_quality:str; agreement_ratio:float; conflict_ratio:float; buy_score:float; sell_score:float; neutral_score:float; dominant_sources:tuple[str,...]; contradicting_sources:tuple[str,...]; expected_next_action_en:str; expected_next_action_th:str; next_review_time_utc:str; contributions:tuple[ConsensusContribution,...]; direct_execution:bool=False
