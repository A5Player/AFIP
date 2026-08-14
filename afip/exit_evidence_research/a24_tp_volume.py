"""A24 TP-approach buffer and volume-aware holding/exit research.

This module emits advisory evidence only.  It never imports an execution
gateway and never sends, modifies, partially closes, or closes an order.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from statistics import mean
from typing import Any, Iterable, Mapping

from afip.historical_replay_research import AppendOnlyResearchDataset

_ACTIONS = {"HOLD", "PROTECT", "EXIT_WATCH", "PARTIAL_EXIT", "FULL_EXIT", "RUNNER"}
_DIRECTIONS = {"BUY", "SELL"}


def _identifier(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()[:20].upper()


@dataclass(frozen=True)
class A24TPVolumePolicy:
    minimum_buffer_points: float = 10.0
    atr_buffer_fraction: float = 0.20
    maximum_buffer_r: float = 0.50
    weak_volume_ratio: float = 0.80
    strong_volume_ratio: float = 1.20
    reversal_wick_ratio: float = 0.55
    protect_giveback_r: float = 0.35
    minimum_volume_samples: int = 20

    def __post_init__(self) -> None:
        numeric = (self.minimum_buffer_points, self.atr_buffer_fraction, self.maximum_buffer_r,
                   self.weak_volume_ratio, self.strong_volume_ratio, self.reversal_wick_ratio,
                   self.protect_giveback_r)
        if not all(isfinite(value) and value >= 0 for value in numeric):
            raise ValueError("A24 policy values must be finite and non-negative")
        if self.minimum_volume_samples <= 0 or self.weak_volume_ratio >= self.strong_volume_ratio:
            raise ValueError("A24 volume thresholds are invalid")
        if not 0 <= self.reversal_wick_ratio <= 1:
            raise ValueError("A24 reversal wick ratio must be within zero and one")


@dataclass(frozen=True)
class A24DecisionContext:
    research_case_id: str
    decision_timestamp_utc: str
    direction: str
    current_price: float
    target_price: float
    point_size: float
    initial_risk_points: float
    atr_points: float
    spread_points: float
    tick_volume: float
    volume_baseline: float
    volume_sample_size: int
    favorable_wick_ratio: float
    unrealized_r: float
    maximum_favorable_r: float
    position_units: int
    holding_bars: int
    timeframe: str
    market_regime: str
    session_name: str
    event_window: str
    calendar_context: str
    volume_source: str = "MT5_TICK_VOLUME"
    decision_uses_closed_bar_data_only: bool = True
    future_data_used: bool = False

    def __post_init__(self) -> None:
        required = (self.research_case_id, self.decision_timestamp_utc, self.timeframe,
                    self.market_regime, self.session_name, self.event_window, self.calendar_context)
        if not all(str(value).strip() for value in required) or self.direction not in _DIRECTIONS:
            raise ValueError("A24 decision identity or direction is invalid")
        numeric = (self.current_price, self.target_price, self.point_size, self.initial_risk_points,
                   self.atr_points, self.spread_points, self.tick_volume, self.volume_baseline,
                   self.favorable_wick_ratio, self.unrealized_r, self.maximum_favorable_r)
        if not all(isfinite(value) for value in numeric):
            raise ValueError("A24 decision values must be finite")
        if min(self.point_size, self.initial_risk_points) <= 0 or min(
                self.atr_points, self.spread_points, self.tick_volume, self.volume_baseline) < 0:
            raise ValueError("A24 distance and volume values are invalid")
        if not 0 <= self.favorable_wick_ratio <= 1 or self.position_units <= 0 or self.holding_bars < 0:
            raise ValueError("A24 position or candle-shape values are invalid")
        if self.volume_source != "MT5_TICK_VOLUME":
            raise ValueError("A24 GOLD# research currently accepts explicit MT5 tick-volume provenance only")
        if not self.decision_uses_closed_bar_data_only or self.future_data_used:
            raise ValueError("A24 decisions must be leakage-free and use closed-bar data only")


@dataclass(frozen=True)
class A24AdvisoryDecision:
    decision_id: str
    research_case_id: str
    decision_timestamp_utc: str
    recommended_action: str
    reason_code: str
    approach_buffer_points: float
    distance_to_target_points: float
    within_approach_buffer: bool
    target_reached: bool
    volume_ratio: float | None
    volume_state: str
    volume_source: str
    timeframe: str
    market_regime: str
    session_name: str
    event_window: str
    calendar_context: str
    position_units: int
    holding_bars: int
    unrealized_r: float
    maximum_favorable_r: float
    research_only: bool = True
    no_order_sent: bool = True
    automatic_promotion_allowed: bool = False
    execution_authority: str = "NONE"

    def __post_init__(self) -> None:
        if self.recommended_action not in _ACTIONS:
            raise ValueError("A24 advisory action is invalid")
        if not self.research_only or not self.no_order_sent or self.automatic_promotion_allowed:
            raise ValueError("A24 advisory cannot acquire order or promotion authority")
        if self.execution_authority != "NONE":
            raise ValueError("A24 advisory has no execution authority")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class A24OutcomeEvidence:
    decision_id: str
    outcome_timestamp_utc: str
    realized_r: float
    execution_cost_r: float
    swap_cost_r: float
    mfe_r: float
    mae_r: float
    holding_seconds: int
    outcome_evaluation_uses_subsequent_closed_bars: bool = True
    future_data_used_for_decision: bool = False
    research_only: bool = True
    execution_authority: str = "NONE"

    def __post_init__(self) -> None:
        values = (self.realized_r, self.execution_cost_r, self.swap_cost_r, self.mfe_r, self.mae_r)
        if not self.decision_id.strip() or not self.outcome_timestamp_utc.strip() or not all(isfinite(v) for v in values):
            raise ValueError("A24 outcome identity or values are invalid")
        if min(self.execution_cost_r, self.swap_cost_r, self.mfe_r, self.mae_r) < 0 or self.holding_seconds < 0:
            raise ValueError("A24 outcome costs and excursions cannot be negative")
        if not self.outcome_evaluation_uses_subsequent_closed_bars or self.future_data_used_for_decision:
            raise ValueError("A24 outcome must be blind-forward and decision leakage-free")
        if not self.research_only or self.execution_authority != "NONE":
            raise ValueError("A24 outcome has no execution authority")

    @property
    def net_realized_r(self) -> float:
        return self.realized_r - self.execution_cost_r - self.swap_cost_r

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["net_realized_r"] = self.net_realized_r
        return value


@dataclass(frozen=True)
class A24ActionSummary:
    recommended_action: str
    timeframe: str
    market_regime: str
    session_name: str
    sample_size: int
    expectancy_after_cost_r: float
    average_holding_seconds: float
    automatic_promotion_allowed: bool = False
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class A24TPVolumeResearch:
    """Produce deterministic advisory decisions and blind-forward evidence."""

    def __init__(self, dataset: AppendOnlyResearchDataset, policy: A24TPVolumePolicy | None = None) -> None:
        self.dataset = dataset
        self.policy = policy or A24TPVolumePolicy()

    def advise(self, context: A24DecisionContext) -> A24AdvisoryDecision:
        risk_cap = context.initial_risk_points * self.policy.maximum_buffer_r
        buffer_points = min(risk_cap, max(self.policy.minimum_buffer_points,
                                          context.atr_points * self.policy.atr_buffer_fraction,
                                          context.spread_points))
        signed_distance = ((context.target_price - context.current_price) / context.point_size
                           if context.direction == "BUY" else
                           (context.current_price - context.target_price) / context.point_size)
        target_reached = signed_distance <= 0
        within = signed_distance <= buffer_points
        sufficient = context.volume_sample_size >= self.policy.minimum_volume_samples and context.volume_baseline > 0
        ratio = context.tick_volume / context.volume_baseline if sufficient else None
        volume_state = ("INSUFFICIENT" if ratio is None else "WEAK" if ratio < self.policy.weak_volume_ratio
                        else "STRONG" if ratio >= self.policy.strong_volume_ratio else "NORMAL")
        giveback = max(0.0, context.maximum_favorable_r - context.unrealized_r)
        reversal = context.favorable_wick_ratio >= self.policy.reversal_wick_ratio

        if target_reached:
            action, reason = "FULL_EXIT", "research_target_reached"
        elif not within:
            action, reason = "HOLD", "outside_tp_approach_buffer"
        elif volume_state == "INSUFFICIENT":
            action, reason = "EXIT_WATCH", "tp_buffer_volume_evidence_insufficient"
        elif giveback >= self.policy.protect_giveback_r:
            action, reason = "PROTECT", "tp_buffer_profit_giveback"
        elif volume_state == "STRONG" and not reversal:
            action = "RUNNER" if context.position_units >= 2 else "HOLD"
            reason = "tp_buffer_favorable_volume_continuation"
        elif volume_state == "WEAK" or reversal:
            action = "PARTIAL_EXIT" if context.position_units >= 2 else "EXIT_WATCH"
            reason = "tp_buffer_weak_volume_or_reversal"
        else:
            action, reason = "HOLD", "tp_buffer_neutral_volume_hold"
        base = {**asdict(context), "action": action, "reason": reason,
                "buffer_points": buffer_points, "distance_points": signed_distance}
        decision = A24AdvisoryDecision(
            decision_id=f"A24-{_identifier(base)}", research_case_id=context.research_case_id,
            decision_timestamp_utc=context.decision_timestamp_utc, recommended_action=action,
            reason_code=reason, approach_buffer_points=buffer_points,
            distance_to_target_points=max(0.0, signed_distance), within_approach_buffer=within,
            target_reached=target_reached, volume_ratio=ratio, volume_state=volume_state,
            volume_source=context.volume_source, timeframe=context.timeframe,
            market_regime=context.market_regime, session_name=context.session_name,
            event_window=context.event_window, calendar_context=context.calendar_context,
            position_units=context.position_units, holding_bars=context.holding_bars,
            unrealized_r=context.unrealized_r, maximum_favorable_r=context.maximum_favorable_r)
        existing = {str(item["record"].get("decision_id"))
                    for item in self.dataset.records("a24_tp_volume_decisions")}
        if decision.decision_id in existing:
            raise ValueError("A24 advisory decision already exists")
        self.dataset.append("a24_tp_volume_decisions", decision.as_dict())
        return decision

    def record_outcome(self, outcome: A24OutcomeEvidence) -> None:
        decisions = {str(item["record"].get("decision_id")): item["record"]
                     for item in self.dataset.records("a24_tp_volume_decisions")}
        if outcome.decision_id not in decisions:
            raise ValueError("A24 outcome requires a recorded advisory decision")
        if any(item["record"].get("decision_id") == outcome.decision_id
               for item in self.dataset.records("a24_tp_volume_outcomes")):
            raise ValueError("A24 outcome for this decision already exists")
        decision = decisions[outcome.decision_id]
        self.dataset.append("a24_tp_volume_outcomes", outcome.as_dict())
        # Feed the existing A22 validator without changing its authority.  The
        # timestamp is the decision timestamp, never the outcome timestamp.
        self.dataset.append("a22_holding_exit_validation_observations", {
            "decision_timestamp_utc": decision["decision_timestamp_utc"],
            "policy_id": f"A24:{decision['recommended_action']}",
            "holding_bucket_id": "TP_APPROACH_BUFFER",
            "timeframe": decision["timeframe"], "market_regime": decision["market_regime"],
            "session_name": decision["session_name"], "event_window": decision["event_window"],
            "calendar_context": decision["calendar_context"],
            "net_realized_r": outcome.net_realized_r, "mfe_r": outcome.mfe_r,
            "mae_r": outcome.mae_r, "holding_seconds": outcome.holding_seconds,
            "source_decision_id": outcome.decision_id, "research_only": True,
            "automatic_promotion_allowed": False, "execution_authority": "NONE",
        })

    def summarize(self, minimum_sample_size: int = 30) -> tuple[A24ActionSummary, ...]:
        if minimum_sample_size <= 0:
            raise ValueError("A24 minimum sample size must be positive")
        decisions = {item["record"]["decision_id"]: item["record"]
                     for item in self.dataset.records("a24_tp_volume_decisions")}
        grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
        for envelope in self.dataset.records("a24_tp_volume_outcomes"):
            outcome = envelope["record"]; decision = decisions.get(outcome.get("decision_id"))
            if decision is None:
                continue
            key = (str(decision["recommended_action"]), str(decision["timeframe"]),
                   str(decision["market_regime"]), str(decision["session_name"]))
            grouped.setdefault(key, []).append(outcome)
        summaries = tuple(A24ActionSummary(*key, len(values),
                    mean(float(item["net_realized_r"]) for item in values),
                    mean(float(item["holding_seconds"]) for item in values))
                    for key, values in sorted(grouped.items()) if len(values) >= minimum_sample_size)
        for item in summaries:
            self.dataset.append("a24_tp_volume_summaries", item.as_dict())
        return summaries
