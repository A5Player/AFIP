"""A16 exit evidence context and research-only ranking."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from statistics import mean
from typing import Iterable

@dataclass(frozen=True)
class A16ExitObservation:
    policy_id: str; realized_r: float; mfe_r: float; mae_r: float; giveback_r: float
    pattern_id: str; plan_id: str; market_regime: str; session_name: str
    event_window: str; calendar_context: str; execution_cost_r: float
    future_data_used: bool = False
    outcome_evaluation_uses_subsequent_closed_bars: bool = True
    research_state: str = "EXPERIMENTAL"; production_usable: bool = False
    def __post_init__(self) -> None:
        if not all(str(getattr(self, n)).strip() for n in ("policy_id","pattern_id","plan_id","market_regime","session_name","event_window","calendar_context")):
            raise ValueError("A16 observation context is incomplete")
        if self.future_data_used or not self.outcome_evaluation_uses_subsequent_closed_bars:
            raise ValueError("A16 evidence must be blind-forward and free of future data")
        if self.research_state != "EXPERIMENTAL" or self.production_usable:
            raise ValueError("A16 evidence remains research-only")
        if min(self.mfe_r, self.mae_r, self.giveback_r, self.execution_cost_r) < 0:
            raise ValueError("A16 evidence metrics cannot be negative")
    def as_dict(self) -> dict[str, object]: return asdict(self)

@dataclass(frozen=True)
class A16PolicyRanking:
    policy_id: str; sample_size: int; expectancy_after_cost_r: float; win_rate: float
    average_mfe_r: float; average_mae_r: float; average_giveback_r: float; research_rank: int
    automatic_promotion_allowed: bool = False; production_usable: bool = False

def rank_a16_policies(observations: Iterable[A16ExitObservation], minimum_sample_size: int = 30) -> tuple[A16PolicyRanking, ...]:
    if minimum_sample_size <= 0: raise ValueError("minimum sample size must be positive")
    grouped: dict[str, list[A16ExitObservation]] = {}
    for item in observations: grouped.setdefault(item.policy_id, []).append(item)
    if not grouped: raise ValueError("at least one observation is required")
    ranked = [(key, values, mean(x.realized_r-x.execution_cost_r for x in values)) for key, values in grouped.items() if len(values) >= minimum_sample_size]
    ranked.sort(key=lambda item: (-item[2], item[0]))
    return tuple(A16PolicyRanking(key, len(values), exp, sum(x.realized_r>0 for x in values)/len(values), mean(x.mfe_r for x in values), mean(x.mae_r for x in values), mean(x.giveback_r for x in values), n) for n,(key,values,exp) in enumerate(ranked,1))
