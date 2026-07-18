"""Milestone T Pack 2: chronological replay and position-management research.

Research-only foundation. It never sends, modifies, or closes MT5 orders and it
never changes production trading logic. All observations are deterministic,
chronological, and suitable for storage inside the Pack 1 research quarantine.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence


class LegRole(str, Enum):
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"
    DYNAMIC = "DYNAMIC"


class ExitAction(str, Enum):
    HOLD = "HOLD"
    CLOSE_ALL = "CLOSE_ALL"
    CLOSE_ONE_LEG = "CLOSE_ONE_LEG"
    MOVE_STOP_TO_BREAK_EVEN = "MOVE_STOP_TO_BREAK_EVEN"
    TRAIL_STOP = "TRAIL_STOP"
    PYRAMID_ADD = "PYRAMID_ADD"
    NO_PYRAMID = "NO_PYRAMID"


@dataclass(frozen=True)
class ReplayCandle:
    timestamp_utc: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReplayCandle":
        return cls(
            timestamp_utc=str(value["timestamp_utc"]),
            open=float(value["open"]),
            high=float(value["high"]),
            low=float(value["low"]),
            close=float(value["close"]),
            volume=float(value.get("volume", 0.0)),
        )


@dataclass(frozen=True)
class ReplayDecisionContext:
    replay_index: int
    replay_timestamp_utc: str
    visible_candle_count: int
    latest_close: float
    future_candle_count: int
    future_data_exposed: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PositionLegPlan:
    leg_id: str
    role: LegRole
    quantity_units: int = 1
    fixed_target_price: float | None = None
    fixed_stop_price: float | None = None
    allow_overnight_hold: bool = False
    allow_dynamic_exit: bool = True

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["role"] = self.role.value
        return payload


@dataclass(frozen=True)
class AlternativeDecision:
    alternative_id: str
    action: ExitAction
    affected_leg_ids: tuple[str, ...] = ()
    rationale_code: str = "research_alternative"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["action"] = self.action.value
        return payload


@dataclass(frozen=True)
class PathMetrics:
    direction: str
    entry_price: float
    final_price: float
    maximum_favorable_excursion: float
    maximum_adverse_excursion: float
    time_to_maximum_favorable_excursion_bars: int
    time_to_maximum_adverse_excursion_bars: int
    final_return: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PyramidEligibility:
    allowed: bool
    reason: str
    block_reasons: tuple[str, ...]
    current_total_risk: float
    maximum_total_risk: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchReplayRecord:
    research_run_id: str
    dataset_version: str
    market_context_signature: str
    setup_id: str
    direction: str
    entry_timestamp_utc: str
    entry_price: float
    replay_verified: bool
    future_leakage_detected: bool
    leg_plans: tuple[dict[str, Any], ...]
    decision_alternatives: tuple[dict[str, Any], ...]
    path_metrics: dict[str, Any]
    post_exit_observations: dict[str, float | None]
    pyramid_research: dict[str, Any]
    research_state: str
    record_checksum: str
    created_at_utc: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ChronologicalReplay:
    """Expose candles one step at a time and fail on non-monotonic time."""

    def __init__(self, candles: Sequence[ReplayCandle | Mapping[str, Any]]) -> None:
        self._candles = tuple(
            candle if isinstance(candle, ReplayCandle) else ReplayCandle.from_mapping(candle)
            for candle in candles
        )
        if not self._candles:
            raise ValueError("chronological replay requires at least one candle")
        timestamps = [self._parse_timestamp(c.timestamp_utc) for c in self._candles]
        if timestamps != sorted(timestamps) or len(set(timestamps)) != len(timestamps):
            raise ValueError("replay candles must have unique strictly increasing timestamps")

    @property
    def candle_count(self) -> int:
        return len(self._candles)

    def context_at(self, replay_index: int) -> ReplayDecisionContext:
        if replay_index < 0 or replay_index >= len(self._candles):
            raise IndexError("replay index outside available candle range")
        visible = self._candles[: replay_index + 1]
        return ReplayDecisionContext(
            replay_index=replay_index,
            replay_timestamp_utc=visible[-1].timestamp_utc,
            visible_candle_count=len(visible),
            latest_close=visible[-1].close,
            future_candle_count=len(self._candles) - len(visible),
            future_data_exposed=False,
        )

    def visible_candles(self, replay_index: int) -> tuple[ReplayCandle, ...]:
        self.context_at(replay_index)
        return self._candles[: replay_index + 1]

    def outcome_candles(self, entry_index: int) -> tuple[ReplayCandle, ...]:
        if entry_index < 0 or entry_index >= len(self._candles):
            raise IndexError("entry index outside available candle range")
        return self._candles[entry_index:]

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("replay timestamps must include timezone information")
        return parsed.astimezone(timezone.utc)


class PositionPathAnalyzer:
    @staticmethod
    def analyze(
        candles: Sequence[ReplayCandle], *, direction: str, entry_price: float
    ) -> PathMetrics:
        if not candles:
            raise ValueError("path analysis requires candles")
        normalized_direction = direction.strip().upper()
        if normalized_direction not in {"BUY", "SELL"}:
            raise ValueError("direction must be BUY or SELL")
        favorable: list[float] = []
        adverse: list[float] = []
        for candle in candles:
            if normalized_direction == "BUY":
                favorable.append(candle.high - entry_price)
                adverse.append(entry_price - candle.low)
            else:
                favorable.append(entry_price - candle.low)
                adverse.append(candle.high - entry_price)
        maximum_favorable = max(0.0, max(favorable))
        maximum_adverse = max(0.0, max(adverse))
        final_price = candles[-1].close
        final_return = final_price - entry_price if normalized_direction == "BUY" else entry_price - final_price
        return PathMetrics(
            direction=normalized_direction,
            entry_price=entry_price,
            final_price=final_price,
            maximum_favorable_excursion=maximum_favorable,
            maximum_adverse_excursion=maximum_adverse,
            time_to_maximum_favorable_excursion_bars=favorable.index(max(favorable)),
            time_to_maximum_adverse_excursion_bars=adverse.index(max(adverse)),
            final_return=final_return,
        )


class DynamicPyramidResearchGate:
    """Research whether an additional unit would have been risk-permissible.

    The gate is intentionally stricter than a simple overnight rule. Holding
    across a date boundary may make a position eligible for evaluation, but it
    never grants an add automatically.
    """

    @staticmethod
    def evaluate(record: Mapping[str, Any]) -> PyramidEligibility:
        blocked: list[str] = []
        current_risk = float(record.get("current_total_risk", 0.0))
        added_risk = float(record.get("proposed_added_risk", 0.0))
        maximum_risk = float(record.get("maximum_total_risk", 0.0))
        if not bool(record.get("position_profitable", False)):
            blocked.append("position_not_profitable")
        if not bool(record.get("risk_reduced", False)):
            blocked.append("existing_risk_not_reduced")
        if not bool(record.get("market_regime_supportive", False)):
            blocked.append("market_regime_not_supportive")
        if not bool(record.get("structure_intact", False)):
            blocked.append("market_structure_not_intact")
        if not bool(record.get("trend_supportive", False)):
            blocked.append("trend_not_supportive")
        if bool(record.get("future_leakage_detected", False)):
            blocked.append("future_leakage_detected")
        if added_risk <= 0.0:
            blocked.append("valid_added_risk_required")
        if maximum_risk <= 0.0 or current_risk + added_risk > maximum_risk:
            blocked.append("maximum_total_risk_exceeded")
        allowed = not blocked
        return PyramidEligibility(
            allowed=allowed,
            reason="pyramid_research_eligible" if allowed else "pyramid_research_blocked",
            block_reasons=tuple(sorted(set(blocked))),
            current_total_risk=current_risk + (added_risk if allowed else 0.0),
            maximum_total_risk=maximum_risk,
        )


class DecisionAlternativeRegistry:
    """Create auditable alternatives without selecting a production action."""

    DEFAULT_ACTIONS = (
        ExitAction.HOLD,
        ExitAction.CLOSE_ALL,
        ExitAction.CLOSE_ONE_LEG,
        ExitAction.MOVE_STOP_TO_BREAK_EVEN,
        ExitAction.TRAIL_STOP,
        ExitAction.PYRAMID_ADD,
        ExitAction.NO_PYRAMID,
    )

    @classmethod
    def build(cls, leg_ids: Iterable[str]) -> tuple[AlternativeDecision, ...]:
        normalized_leg_ids = tuple(str(value).strip() for value in leg_ids if str(value).strip())
        alternatives: list[AlternativeDecision] = []
        for index, action in enumerate(cls.DEFAULT_ACTIONS, start=1):
            affected = normalized_leg_ids
            if action == ExitAction.CLOSE_ONE_LEG:
                affected = normalized_leg_ids[:1]
            alternatives.append(
                AlternativeDecision(
                    alternative_id=f"ALT-{index:02d}",
                    action=action,
                    affected_leg_ids=affected,
                    rationale_code=f"research_{action.value.lower()}",
                )
            )
        return tuple(alternatives)


class ResearchReplayBuilder:
    """Build a quarantined record from a deterministic replay outcome."""

    @staticmethod
    def build(
        *,
        research_run_id: str,
        dataset_version: str,
        market_context_signature: str,
        setup_id: str,
        replay: ChronologicalReplay,
        entry_index: int,
        direction: str,
        leg_plans: Sequence[PositionLegPlan],
        post_exit_observations: Mapping[str, float | None] | None = None,
        pyramid_inputs: Mapping[str, Any] | None = None,
        now: datetime | None = None,
    ) -> ResearchReplayRecord:
        required = {
            "research_run_id": research_run_id,
            "dataset_version": dataset_version,
            "market_context_signature": market_context_signature,
            "setup_id": setup_id,
        }
        missing = [key for key, value in required.items() if not str(value).strip()]
        if missing:
            raise ValueError(f"required replay identifiers missing: {', '.join(sorted(missing))}")
        if not leg_plans or len(leg_plans) > 3:
            raise ValueError("research plan must contain between one and three position legs")
        if len({leg.leg_id for leg in leg_plans}) != len(leg_plans):
            raise ValueError("position leg identifiers must be unique")

        decision_context = replay.context_at(entry_index)
        entry_price = decision_context.latest_close
        outcome = replay.outcome_candles(entry_index)
        metrics = PositionPathAnalyzer.analyze(outcome, direction=direction, entry_price=entry_price)
        alternatives = DecisionAlternativeRegistry.build(leg.leg_id for leg in leg_plans)
        pyramid_result = DynamicPyramidResearchGate.evaluate(pyramid_inputs or {})
        timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        payload = {
            "research_run_id": research_run_id,
            "dataset_version": dataset_version,
            "market_context_signature": market_context_signature,
            "setup_id": setup_id,
            "direction": direction.strip().upper(),
            "entry_timestamp_utc": decision_context.replay_timestamp_utc,
            "entry_price": entry_price,
            "replay_verified": not decision_context.future_data_exposed,
            "future_leakage_detected": decision_context.future_data_exposed,
            "leg_plans": [leg.as_dict() for leg in leg_plans],
            "decision_alternatives": [alternative.as_dict() for alternative in alternatives],
            "path_metrics": metrics.as_dict(),
            "post_exit_observations": dict(post_exit_observations or {}),
            "pyramid_research": pyramid_result.as_dict(),
            "research_state": "EXPERIMENTAL",
            "created_at_utc": timestamp,
        }
        checksum = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return ResearchReplayRecord(
            record_checksum=checksum,
            **payload,
        )


__all__ = [
    "AlternativeDecision",
    "ChronologicalReplay",
    "DecisionAlternativeRegistry",
    "DynamicPyramidResearchGate",
    "ExitAction",
    "LegRole",
    "PathMetrics",
    "PositionLegPlan",
    "PositionPathAnalyzer",
    "PyramidEligibility",
    "ReplayCandle",
    "ReplayDecisionContext",
    "ResearchReplayBuilder",
    "ResearchReplayRecord",
]
