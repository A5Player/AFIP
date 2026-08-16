"""A21 chronological producer for A20 holding/exit evidence; research-only."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Iterable

from afip.exit_outcome_research import A16ExitResearchRunner, A16PolicySet, A16ResearchContext
from afip.exit_outcome_research.runtime import ExitPolicyExperimentRunner, PositionResearchCase
from afip.historical_replay_research import AppendOnlyResearchDataset
from afip.research_replay import ReplayCandle

from .a20_holding_exit import A20HoldingExitObservation, A20HoldingExitRanking, A20HoldingExitResearch


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class A21HoldingBucket:
    bucket_id: str
    maximum_holding_bars: int | None

    def __post_init__(self) -> None:
        if not self.bucket_id.strip():
            raise ValueError("holding bucket id is required")
        if self.maximum_holding_bars is not None and self.maximum_holding_bars <= 0:
            raise ValueError("holding bucket maximum must be positive")


@dataclass(frozen=True)
class A21ProductionResult:
    observations: tuple[A20HoldingExitObservation, ...]
    rankings: tuple[A20HoldingExitRanking, ...]
    research_only: bool = True
    execution_authority: str = "NONE"


class A21HoldingExitEvidenceProducer:
    """Run existing exit replay and persist A20 observations exactly once per case."""

    def __init__(self, dataset: AppendOnlyResearchDataset, *, buckets: Iterable[A21HoldingBucket],
                 minimum_sample_size: int = 30) -> None:
        values = tuple(buckets)
        if not values:
            raise ValueError("at least one holding bucket is required")
        finite = [item.maximum_holding_bars for item in values if item.maximum_holding_bars is not None]
        if finite != sorted(finite) or len(finite) != len(set(finite)):
            raise ValueError("holding bucket maxima must be unique and ascending")
        if values[-1].maximum_holding_bars is not None or any(item.maximum_holding_bars is None for item in values[:-1]):
            raise ValueError("the final holding bucket must be the only unbounded bucket")
        self.dataset = dataset
        self.buckets = values
        self.research = A20HoldingExitResearch(dataset, minimum_sample_size)

    def produce(self, *, case: PositionResearchCase, policy_set: A16PolicySet,
                candles: Iterable[ReplayCandle | dict[str, object]], context: A16ResearchContext,
                timeframe: str, execution_cost_r: float, swap_cost_per_second_r: float = 0.0) -> A21ProductionResult:
        if not timeframe.strip():
            raise ValueError("timeframe is required")
        if execution_cost_r < 0 or swap_cost_per_second_r < 0:
            raise ValueError("research costs cannot be negative")
        if any(envelope["record"].get("research_case_id") == case.position_case_id
               for envelope in self.dataset.records("a20_holding_exit_observations")):
            raise ValueError("holding/exit evidence for this research case already exists")
        bars = tuple(value if isinstance(value, ReplayCandle) else ReplayCandle.from_mapping(value)
                     for value in candles)
        if case.entry_index < 0 or case.entry_index + 1 >= len(bars):
            raise ValueError("at least one subsequent closed bar is required after entry")
        timestamps = [bar.timestamp_utc for bar in bars]
        if timestamps != sorted(timestamps) or len(timestamps) != len(set(timestamps)):
            raise ValueError("replay candles must be unique and chronological")

        # Entry is known at the close of entry_index. Evaluation starts strictly
        # on the next closed bar, preventing same-entry-bar future leakage.
        evaluation_case = replace(case, entry_index=case.entry_index + 1)
        outcomes = A16ExitResearchRunner(ExitPolicyExperimentRunner(self.dataset)).run(
            case=evaluation_case, policy_set=policy_set, candles=bars,
        )
        entry_time = _timestamp(bars[case.entry_index].timestamp_utc)
        observations: list[A20HoldingExitObservation] = []
        for outcome in outcomes:
            holding_seconds = max(0, int((_timestamp(outcome.exit_timestamp_utc) - entry_time).total_seconds()))
            action = "HOLD" if outcome.exit_reason == "END_OF_REPLAY" else "FULL_EXIT"
            if outcome.policy_id == "PARTIAL_RUNNER":
                action = "RUNNER"
            observation = A20HoldingExitObservation(
                research_case_id=case.position_case_id, policy_id=outcome.policy_id,
                holding_bucket_id=self._bucket(outcome.bars_held), recommended_action=action,
                timeframe=timeframe, market_regime=context.market_regime,
                session_name=context.session_name, event_window=context.event_window,
                calendar_context=context.calendar_context, position_units=case.position_units,
                holding_bars=outcome.bars_held, holding_seconds=holding_seconds,
                realized_r=outcome.realized_r, mfe_r=outcome.maximum_favorable_excursion_r,
                mae_r=outcome.maximum_adverse_excursion_r,
                giveback_r=outcome.missed_profit_r, missed_profit_r=outcome.missed_profit_r,
                execution_cost_r=execution_cost_r,
                swap_cost_r=holding_seconds * swap_cost_per_second_r,
                future_data_used=context.future_data_used,
                outcome_evaluation_uses_subsequent_closed_bars=context.outcome_evaluation_uses_subsequent_closed_bars,
            )
            observations.append(observation)
        self.research.record(observations)
        for observation in observations:
            source = observation.as_dict()
            source["decision_timestamp_utc"] = context.decision_timestamp_utc
            source["outcome_method"] = context.outcome_evaluation_method
            source["decision_score_percent"] = context.decision_score_percent
            source["pattern_family"] = context.pattern_family
            self.dataset.append("a22_holding_exit_validation_observations", source)
        return A21ProductionResult(tuple(observations), self.research.rank_recorded())

    def _bucket(self, holding_bars: int) -> str:
        return next(item.bucket_id for item in self.buckets
                    if item.maximum_holding_bars is None or holding_bars <= item.maximum_holding_bars)
