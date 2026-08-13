"""A20 joint holding-duration and exit-policy research; never executes orders."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Iterable

from afip.historical_replay_research import AppendOnlyResearchDataset

_ACTIONS = {"HOLD", "PROTECT", "EXIT_WATCH", "PARTIAL_EXIT", "FULL_EXIT", "RUNNER"}


@dataclass(frozen=True)
class A20HoldingExitObservation:
    research_case_id: str
    policy_id: str
    holding_bucket_id: str
    recommended_action: str
    timeframe: str
    market_regime: str
    session_name: str
    event_window: str
    calendar_context: str
    position_units: int
    holding_bars: int
    holding_seconds: int
    realized_r: float
    mfe_r: float
    mae_r: float
    giveback_r: float
    missed_profit_r: float
    execution_cost_r: float
    swap_cost_r: float = 0.0
    future_data_used: bool = False
    outcome_evaluation_uses_subsequent_closed_bars: bool = True
    research_only: bool = True
    execution_authority: str = "NONE"

    def __post_init__(self) -> None:
        required = ("research_case_id", "policy_id", "holding_bucket_id", "timeframe",
                    "market_regime", "session_name", "event_window", "calendar_context")
        if not all(str(getattr(self, name)).strip() for name in required):
            raise ValueError("A20 holding/exit context is incomplete")
        if self.recommended_action not in _ACTIONS:
            raise ValueError("A20 recommended action is invalid")
        if self.position_units <= 0 or self.holding_bars < 0 or self.holding_seconds < 0:
            raise ValueError("A20 holding quantities are invalid")
        if min(self.mfe_r, self.mae_r, self.giveback_r, self.missed_profit_r,
               self.execution_cost_r, self.swap_cost_r) < 0:
            raise ValueError("A20 evidence metrics cannot be negative")
        if self.recommended_action in {"PARTIAL_EXIT", "RUNNER"} and self.position_units < 2:
            raise ValueError("partial exit and runner research require multiple units")
        if self.future_data_used or not self.outcome_evaluation_uses_subsequent_closed_bars:
            raise ValueError("A20 evidence must be blind-forward and free of future data")
        if not self.research_only or self.execution_authority != "NONE":
            raise ValueError("A20 evidence has no execution authority")

    @property
    def net_realized_r(self) -> float:
        return self.realized_r - self.execution_cost_r - self.swap_cost_r

    def as_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["net_realized_r"] = self.net_realized_r
        return value


@dataclass(frozen=True)
class A20HoldingExitRanking:
    policy_id: str
    holding_bucket_id: str
    timeframe: str
    market_regime: str
    session_name: str
    event_window: str
    calendar_context: str
    sample_size: int
    expectancy_after_cost_r: float
    average_holding_bars: float
    average_holding_seconds: float
    average_mfe_r: float
    average_mae_r: float
    average_giveback_r: float
    average_missed_profit_r: float
    research_rank: int
    automatic_promotion_allowed: bool = False
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class A20HoldingExitResearch:
    """Append evidence and rank holding/exit combinations within like contexts."""

    def __init__(self, dataset: AppendOnlyResearchDataset, minimum_sample_size: int = 30) -> None:
        if minimum_sample_size <= 0:
            raise ValueError("minimum sample size must be positive")
        self.dataset = dataset
        self.minimum_sample_size = minimum_sample_size

    def record(self, observations: Iterable[A20HoldingExitObservation]) -> int:
        values = tuple(observations)
        for item in values:
            self.dataset.append("a20_holding_exit_observations", item.as_dict())
        return len(values)

    def rank_recorded(self) -> tuple[A20HoldingExitRanking, ...]:
        observations = tuple(self._from_record(envelope["record"])
                             for envelope in self.dataset.records("a20_holding_exit_observations"))
        grouped: dict[tuple[str, ...], list[A20HoldingExitObservation]] = {}
        for item in observations:
            key = (item.policy_id, item.holding_bucket_id, item.timeframe, item.market_regime,
                   item.session_name, item.event_window, item.calendar_context)
            grouped.setdefault(key, []).append(item)
        eligible = [(key, values) for key, values in grouped.items()
                    if len(values) >= self.minimum_sample_size]
        eligible.sort(key=lambda pair: (-mean(item.net_realized_r for item in pair[1]), pair[0]))
        rankings = tuple(self._ranking(rank_value, key, values)
                         for rank_value, (key, values) in enumerate(eligible, 1))
        for item in rankings:
            self.dataset.append("a20_holding_exit_rankings", item.as_dict())
        return rankings

    @staticmethod
    def _from_record(record: dict[str, object]) -> A20HoldingExitObservation:
        values = dict(record)
        values.pop("net_realized_r", None)
        return A20HoldingExitObservation(**values)

    @staticmethod
    def _ranking(rank_value: int, key: tuple[str, ...], values: list[A20HoldingExitObservation]) -> A20HoldingExitRanking:
        return A20HoldingExitRanking(
            *key, len(values), mean(item.net_realized_r for item in values),
            mean(item.holding_bars for item in values), mean(item.holding_seconds for item in values),
            mean(item.mfe_r for item in values), mean(item.mae_r for item in values),
            mean(item.giveback_r for item in values), mean(item.missed_profit_r for item in values),
            rank_value,
        )
