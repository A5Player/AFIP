"""Milestone T Pack 4: exit, loss-control, and position-outcome research.

This module is strictly research-only. It evaluates hypothetical position
management alternatives against chronological replay candles, records all
results as EXPERIMENTAL, and never calls or modifies MT5 or production runtime.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence

from afip.historical_replay_research import AppendOnlyResearchDataset
from afip.research_replay import ReplayCandle


def _checksum(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def _bounded(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class ExitResearchPolicy:
    policy_id: str
    initial_risk_distance: float
    profit_target_distance: float | None = None
    break_even_trigger_r: float | None = None
    trailing_trigger_r: float | None = None
    trailing_distance_r: float | None = None
    maximum_holding_bars: int | None = None
    adverse_exit_r: float = 1.0

    def __post_init__(self) -> None:
        if not self.policy_id.strip():
            raise ValueError("policy_id is required")
        if self.initial_risk_distance <= 0:
            raise ValueError("initial_risk_distance must be positive")
        if self.profit_target_distance is not None and self.profit_target_distance <= 0:
            raise ValueError("profit_target_distance must be positive")
        for name in ("break_even_trigger_r", "trailing_trigger_r", "trailing_distance_r"):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.maximum_holding_bars is not None and self.maximum_holding_bars <= 0:
            raise ValueError("maximum_holding_bars must be positive")
        if self.adverse_exit_r <= 0:
            raise ValueError("adverse_exit_r must be positive")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PositionResearchCase:
    position_case_id: str
    replay_id: str
    research_run_id: str
    dataset_version: str
    scenario_id: str
    direction: str
    entry_index: int
    entry_price: float
    position_units: int = 1

    def __post_init__(self) -> None:
        if not all((self.position_case_id, self.replay_id, self.research_run_id, self.dataset_version, self.scenario_id)):
            raise ValueError("all position research identifiers are required")
        if self.direction not in {"BUY", "SELL"}:
            raise ValueError("direction must be BUY or SELL")
        if self.entry_index < 0:
            raise ValueError("entry_index must be non-negative")
        if self.entry_price <= 0:
            raise ValueError("entry_price must be positive")
        if self.position_units <= 0:
            raise ValueError("position_units must be positive")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExitAlternativeRecord:
    position_case_id: str
    policy_id: str
    replay_index: int
    replay_timestamp_utc: str
    action: str
    reason_codes: tuple[str, ...]
    active_stop_price: float
    active_target_price: float | None
    unrealized_r: float
    maximum_favorable_excursion_r: float
    maximum_adverse_excursion_r: float
    bars_held: int
    research_state: str
    production_usable: bool
    record_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PositionOutcome:
    position_case_id: str
    policy_id: str
    exit_index: int
    exit_timestamp_utc: str
    exit_price: float
    exit_reason: str
    outcome_classification: str
    realized_r: float
    maximum_favorable_excursion_r: float
    maximum_adverse_excursion_r: float
    profit_capture_ratio: float
    avoided_loss_r: float
    missed_profit_r: float
    bars_held: int
    capital_preservation_score: float
    exit_quality_score: float
    research_state: str
    production_usable: bool
    outcome_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExitOutcomeResearchEngine:
    """Evaluate one policy against a hypothetical position, bar by bar."""

    def __init__(self, dataset: AppendOnlyResearchDataset) -> None:
        self.dataset = dataset

    @staticmethod
    def _normalize_candles(candles: Iterable[ReplayCandle | Mapping[str, Any]]) -> tuple[ReplayCandle, ...]:
        normalized = tuple(
            value if isinstance(value, ReplayCandle) else ReplayCandle.from_mapping(value)
            for value in candles
        )
        if not normalized:
            raise ValueError("candles are required")
        timestamps = [value.timestamp_utc for value in normalized]
        if timestamps != sorted(timestamps) or len(set(timestamps)) != len(timestamps):
            raise ValueError("candles must have unique chronological timestamps")
        return normalized

    @staticmethod
    def _signed_distance(direction: str, price: float, entry_price: float) -> float:
        return price - entry_price if direction == "BUY" else entry_price - price

    @staticmethod
    def _stop_hit(direction: str, candle: ReplayCandle, stop_price: float) -> bool:
        return candle.low <= stop_price if direction == "BUY" else candle.high >= stop_price

    @staticmethod
    def _target_hit(direction: str, candle: ReplayCandle, target_price: float) -> bool:
        return candle.high >= target_price if direction == "BUY" else candle.low <= target_price

    @staticmethod
    def _conservative_same_bar_exit(
        direction: str,
        candle: ReplayCandle,
        stop_price: float,
        target_price: float | None,
    ) -> tuple[str, float] | None:
        stop_hit = ExitOutcomeResearchEngine._stop_hit(direction, candle, stop_price)
        target_hit = target_price is not None and ExitOutcomeResearchEngine._target_hit(direction, candle, target_price)
        if stop_hit:
            return "STOP_OR_LOSS_CONTROL", stop_price
        if target_hit and target_price is not None:
            return "PROFIT_TARGET", target_price
        return None

    def evaluate(
        self,
        *,
        case: PositionResearchCase,
        policy: ExitResearchPolicy,
        candles: Sequence[ReplayCandle | Mapping[str, Any]],
    ) -> PositionOutcome:
        values = self._normalize_candles(candles)
        if case.entry_index >= len(values):
            raise ValueError("entry_index is outside replay candles")

        risk = policy.initial_risk_distance
        stop_price = case.entry_price - risk if case.direction == "BUY" else case.entry_price + risk
        target_price = None
        if policy.profit_target_distance is not None:
            target_price = (
                case.entry_price + policy.profit_target_distance
                if case.direction == "BUY"
                else case.entry_price - policy.profit_target_distance
            )

        maximum_favorable_r = 0.0
        maximum_adverse_r = 0.0
        exit_index = len(values) - 1
        exit_price = values[-1].close
        exit_reason = "END_OF_REPLAY"
        lifecycle_sequence = 0

        for replay_index in range(case.entry_index, len(values)):
            candle = values[replay_index]
            bars_held = replay_index - case.entry_index + 1
            favorable_price = candle.high if case.direction == "BUY" else candle.low
            adverse_price = candle.low if case.direction == "BUY" else candle.high
            favorable_r = self._signed_distance(case.direction, favorable_price, case.entry_price) / risk
            adverse_r = -self._signed_distance(case.direction, adverse_price, case.entry_price) / risk
            maximum_favorable_r = max(maximum_favorable_r, favorable_r)
            maximum_adverse_r = max(maximum_adverse_r, adverse_r)

            reason_codes: list[str] = []
            action = "HOLD"

            if policy.break_even_trigger_r is not None and maximum_favorable_r >= policy.break_even_trigger_r:
                proposed = case.entry_price
                improves = proposed > stop_price if case.direction == "BUY" else proposed < stop_price
                if improves:
                    stop_price = proposed
                    action = "MOVE_STOP_TO_BREAK_EVEN"
                    reason_codes.append("break_even_trigger_reached")

            if (
                policy.trailing_trigger_r is not None
                and policy.trailing_distance_r is not None
                and maximum_favorable_r >= policy.trailing_trigger_r
            ):
                trailing_distance = risk * policy.trailing_distance_r
                proposed = (
                    favorable_price - trailing_distance
                    if case.direction == "BUY"
                    else favorable_price + trailing_distance
                )
                improves = proposed > stop_price if case.direction == "BUY" else proposed < stop_price
                if improves:
                    stop_price = proposed
                    action = "TRAIL_STOP"
                    reason_codes.append("trailing_trigger_reached")

            bar_exit = self._conservative_same_bar_exit(case.direction, candle, stop_price, target_price)
            if bar_exit is not None:
                exit_reason, exit_price = bar_exit
                action = "CLOSE_POSITION"
                reason_codes.append(exit_reason.lower())
            elif policy.maximum_holding_bars is not None and bars_held >= policy.maximum_holding_bars:
                exit_reason = "MAXIMUM_HOLDING_PERIOD"
                exit_price = candle.close
                action = "CLOSE_POSITION"
                reason_codes.append("maximum_holding_period_reached")
            elif maximum_adverse_r >= policy.adverse_exit_r:
                exit_reason = "ADVERSE_EXCURSION_LIMIT"
                exit_price = candle.close
                action = "CLOSE_POSITION"
                reason_codes.append("adverse_excursion_limit_reached")

            unrealized_r = self._signed_distance(case.direction, candle.close, case.entry_price) / risk
            base = {
                "position_case_id": case.position_case_id,
                "policy_id": policy.policy_id,
                "replay_index": replay_index,
                "replay_timestamp_utc": candle.timestamp_utc,
                "action": action,
                "reason_codes": tuple(reason_codes or ("position_remains_valid",)),
                "active_stop_price": stop_price,
                "active_target_price": target_price,
                "unrealized_r": unrealized_r,
                "maximum_favorable_excursion_r": maximum_favorable_r,
                "maximum_adverse_excursion_r": maximum_adverse_r,
                "bars_held": bars_held,
                "research_state": "EXPERIMENTAL",
                "production_usable": False,
            }
            record = ExitAlternativeRecord(record_checksum=_checksum(base), **base)
            self.dataset.append("exit_alternatives", record.as_dict())
            lifecycle_sequence += 1
            self.dataset.append("position_lifecycles", {
                "position_case_id": case.position_case_id,
                "policy_id": policy.policy_id,
                "lifecycle_sequence": lifecycle_sequence,
                "replay_index": replay_index,
                "replay_timestamp_utc": candle.timestamp_utc,
                "lifecycle_state": "CLOSED" if action == "CLOSE_POSITION" else "OPEN_RESEARCH",
                "management_action": action,
                "research_state": "EXPERIMENTAL",
                "production_usable": False,
            })
            if action == "CLOSE_POSITION":
                exit_index = replay_index
                break

        realized_r = self._signed_distance(case.direction, exit_price, case.entry_price) / risk
        profit_capture_ratio = 0.0 if maximum_favorable_r <= 0 else _bounded(realized_r / maximum_favorable_r, 0.0, 1.0)
        avoided_loss_r = max(0.0, maximum_adverse_r + realized_r) if realized_r < 0 else maximum_adverse_r
        missed_profit_r = max(0.0, maximum_favorable_r - max(realized_r, 0.0))

        if realized_r >= 1.0:
            classification = "STRONG_PROFIT"
        elif realized_r > 0:
            classification = "CONTROLLED_PROFIT"
        elif realized_r == 0:
            classification = "BREAK_EVEN"
        elif realized_r > -1.0:
            classification = "CONTROLLED_LOSS"
        else:
            classification = "FULL_RISK_LOSS"

        capital_preservation_score = _bounded(
            100.0 - (max(0.0, -realized_r) * 60.0) - (maximum_adverse_r * 20.0) + (avoided_loss_r * 20.0),
            0.0,
            100.0,
        )
        exit_quality_score = _bounded(
            (profit_capture_ratio * 55.0)
            + (capital_preservation_score * 0.35)
            + (10.0 if realized_r >= 0 else 0.0),
            0.0,
            100.0,
        )
        base_outcome = {
            "position_case_id": case.position_case_id,
            "policy_id": policy.policy_id,
            "exit_index": exit_index,
            "exit_timestamp_utc": values[exit_index].timestamp_utc,
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "outcome_classification": classification,
            "realized_r": realized_r,
            "maximum_favorable_excursion_r": maximum_favorable_r,
            "maximum_adverse_excursion_r": maximum_adverse_r,
            "profit_capture_ratio": profit_capture_ratio,
            "avoided_loss_r": avoided_loss_r,
            "missed_profit_r": missed_profit_r,
            "bars_held": exit_index - case.entry_index + 1,
            "capital_preservation_score": capital_preservation_score,
            "exit_quality_score": exit_quality_score,
            "research_state": "EXPERIMENTAL",
            "production_usable": False,
        }
        outcome = PositionOutcome(outcome_checksum=_checksum(base_outcome), **base_outcome)
        self.dataset.append("position_outcomes", outcome.as_dict())
        self.dataset.append("exit_quality", {
            "position_case_id": case.position_case_id,
            "policy_id": policy.policy_id,
            "exit_quality_score": exit_quality_score,
            "capital_preservation_score": capital_preservation_score,
            "profit_capture_ratio": profit_capture_ratio,
            "missed_profit_r": missed_profit_r,
            "avoided_loss_r": avoided_loss_r,
            "research_state": "EXPERIMENTAL",
            "production_usable": False,
        })
        return outcome


class ExitPolicyExperimentRunner:
    """Evaluate multiple policies without selecting or promoting a winner."""

    def __init__(self, dataset: AppendOnlyResearchDataset) -> None:
        self.engine = ExitOutcomeResearchEngine(dataset)

    def run(
        self,
        *,
        case: PositionResearchCase,
        policies: Iterable[ExitResearchPolicy],
        candles: Sequence[ReplayCandle | Mapping[str, Any]],
    ) -> tuple[PositionOutcome, ...]:
        values = tuple(policies)
        if not values:
            raise ValueError("at least one exit research policy is required")
        identifiers = [value.policy_id for value in values]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("exit research policy identifiers must be unique")
        return tuple(self.engine.evaluate(case=case, policy=policy, candles=candles) for policy in values)
