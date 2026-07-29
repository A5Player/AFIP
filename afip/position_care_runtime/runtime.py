"""Milestone T Pack 13: position care and exit supervision foundation.

The module evaluates an already-open position against its certified care and
exit plan.  It is deterministic and execution-neutral: it produces supervised
recommendations and audit records but never imports MetaTrader5 and never
modifies or closes an order.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afip.complete_trade_plan import CompleteTradePlan
from afip.historical_replay_research import AppendOnlyResearchDataset


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _checksum(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PositionCareSnapshot:
    snapshot_id: str
    plan_id: str
    profile_id: str
    symbol: str
    ticket: str
    direction: str
    entry_price: float
    current_price: float
    initial_stop_price: float
    current_stop_price: float
    current_take_profit_price: float
    volume_lots: float
    unrealized_profit: float
    favorable_points: float
    adverse_points: float
    holding_seconds: int
    market_regime_valid: bool
    thesis_valid: bool
    structure_valid: bool
    volatility_acceptable: bool
    liquidity_acceptable: bool
    market_data_fresh: bool
    connection_ready: bool
    account_state_reconciled: bool
    break_even_triggered: bool
    trailing_triggered: bool
    partial_close_triggered: bool
    target_reached: bool
    hard_invalidation_reached: bool
    emergency_condition_active: bool
    observed_at: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["snapshot_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class PositionCareDecision:
    decision_id: str
    snapshot_id: str
    plan_id: str
    profile_id: str
    ticket: str
    status: str
    recommended_action: str
    reason_codes: tuple[str, ...]
    holding_reason: str
    proposed_stop_price: float
    proposed_take_profit_price: float
    proposed_close_fraction: float
    execution_permission: bool
    decided_at: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["decision_checksum"] = _checksum(payload)
        return payload


class PositionCareSupervisor:
    """Recommend care or exit action while preserving external execution gates."""

    EXECUTION_PERMISSION = False

    def __init__(self, dataset_root: str | Path | None = None) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root) if dataset_root is not None else None

    def evaluate(self, *, plan: CompleteTradePlan, snapshot: PositionCareSnapshot) -> PositionCareDecision:
        reasons: list[str] = []
        action = "HOLD_POSITION"
        status = "SUPERVISION_READY"
        close_fraction = 0.0
        proposed_stop = snapshot.current_stop_price
        proposed_target = snapshot.current_take_profit_price
        holding_reason = plan.care.holding_thesis

        identity_mismatch = (
            snapshot.plan_id != plan.plan_id
            or snapshot.profile_id.upper() != plan.capital.profile_id.upper()
            or snapshot.symbol.upper() != plan.symbol.upper()
            or snapshot.direction.upper() != plan.entry.direction.upper()
        )
        if identity_mismatch:
            reasons.append("position_plan_identity_mismatch")
            action = "ENTER_SAFE_MODE"
            status = "BLOCKED"
        elif not snapshot.connection_ready or not snapshot.market_data_fresh or not snapshot.account_state_reconciled:
            if not snapshot.connection_ready:
                reasons.append("connection_not_ready")
            if not snapshot.market_data_fresh:
                reasons.append("market_data_stale")
            if not snapshot.account_state_reconciled:
                reasons.append("account_state_not_reconciled")
            action = "ENTER_SAFE_MODE"
            status = "BLOCKED"
        elif snapshot.emergency_condition_active:
            reasons.append("emergency_exit_condition_active")
            action = "RECOMMEND_FULL_CLOSE"
            close_fraction = 1.0
        elif snapshot.hard_invalidation_reached:
            reasons.append("hard_invalidation_reached")
            action = "RECOMMEND_FULL_CLOSE"
            close_fraction = 1.0
        elif not snapshot.thesis_valid:
            reasons.append("holding_thesis_failed")
            action = "RECOMMEND_FULL_CLOSE"
            close_fraction = 1.0
        elif not snapshot.market_regime_valid or not snapshot.structure_valid:
            reasons.append("market_structure_no_longer_supports_plan")
            action = "RECOMMEND_FULL_CLOSE"
            close_fraction = 1.0
        elif snapshot.holding_seconds >= plan.care.maximum_holding_seconds:
            reasons.append("maximum_holding_time_reached")
            action = "RECOMMEND_FULL_CLOSE"
            close_fraction = 1.0
        elif snapshot.target_reached:
            reasons.append("profit_target_reached")
            action = "RECOMMEND_FULL_CLOSE"
            close_fraction = 1.0
        elif snapshot.partial_close_triggered and plan.care.partial_close_policy.strip():
            reasons.append("partial_profit_protection_triggered")
            action = "RECOMMEND_PARTIAL_CLOSE"
            close_fraction = 0.5
        elif snapshot.trailing_triggered and plan.care.trailing_policy.strip():
            reasons.append("trailing_stop_update_triggered")
            action = "RECOMMEND_TRAILING_STOP_UPDATE"
            proposed_stop = self._profit_protective_stop(snapshot)
        elif snapshot.break_even_triggered and plan.care.break_even_trigger.strip():
            reasons.append("break_even_update_triggered")
            action = "RECOMMEND_BREAK_EVEN_UPDATE"
            proposed_stop = snapshot.entry_price
        elif not snapshot.volatility_acceptable or not snapshot.liquidity_acceptable:
            reasons.append("market_quality_requires_observation")
            action = "HOLD_WITH_CAUTION"
        else:
            reasons.append("holding_thesis_remains_valid")

        decision_identity = {
            "snapshot_id": snapshot.snapshot_id,
            "plan_id": plan.plan_id,
            "ticket": snapshot.ticket,
            "action": action,
            "reasons": tuple(reasons),
            "proposed_stop": proposed_stop,
        }
        decision = PositionCareDecision(
            decision_id=f"PCD-{_checksum(decision_identity)[:16].upper()}",
            snapshot_id=snapshot.snapshot_id,
            plan_id=plan.plan_id,
            profile_id=snapshot.profile_id,
            ticket=snapshot.ticket,
            status=status,
            recommended_action=action,
            reason_codes=tuple(reasons),
            holding_reason=holding_reason,
            proposed_stop_price=float(proposed_stop),
            proposed_take_profit_price=float(proposed_target),
            proposed_close_fraction=close_fraction,
            execution_permission=self.EXECUTION_PERMISSION,
            decided_at=_utc_now(),
        )
        if self.dataset is not None:
            self.dataset.append("position_care_snapshots", snapshot.as_dict())
            self.dataset.append("position_care_decisions", decision.as_dict())
        return decision

    @staticmethod
    def _profit_protective_stop(snapshot: PositionCareSnapshot) -> float:
        """Return a price-domain protective stop.

        ``favorable_points`` is diagnostic metadata measured in broker points;
        it must never be added directly to a market price.  The safe price
        distance is derived from entry/current prices so the calculation stays
        in one unit domain even when symbol digits differ.
        """
        favorable_price_distance = max(0.0, abs(snapshot.current_price - snapshot.entry_price))
        if snapshot.direction.upper() == "BUY":
            candidate = snapshot.entry_price + favorable_price_distance * 0.5
            return max(snapshot.current_stop_price, candidate)
        candidate = snapshot.entry_price - favorable_price_distance * 0.5
        if snapshot.current_stop_price <= 0:
            return candidate
        return min(snapshot.current_stop_price, candidate)


class PositionCareDashboardReadModelBuilder:
    """Build an explainable, execution-neutral lifecycle view.

    Financial values are only calculated when broker tick metadata is supplied.
    Missing metadata remains ``None`` so the dashboard never invents USD values.
    """

    def build(
        self,
        *,
        snapshot: PositionCareSnapshot,
        decision: PositionCareDecision,
        point_size: float | None = None,
        trade_tick_size: float | None = None,
        trade_tick_value: float | None = None,
    ) -> dict[str, Any]:
        financials = self._financial_provenance(
            snapshot=snapshot,
            decision=decision,
            point_size=point_size,
            trade_tick_size=trade_tick_size,
            trade_tick_value=trade_tick_value,
        )
        record = {
            "profile_id": snapshot.profile_id,
            "symbol": snapshot.symbol,
            "ticket": snapshot.ticket,
            "plan_id": snapshot.plan_id,
            "direction": snapshot.direction,
            "entry_price": snapshot.entry_price,
            "current_price": snapshot.current_price,
            "initial_stop_price": snapshot.initial_stop_price,
            "current_stop_price": snapshot.current_stop_price,
            "proposed_stop_price": decision.proposed_stop_price,
            "current_take_profit_price": snapshot.current_take_profit_price,
            "volume_lots": snapshot.volume_lots,
            "unrealized_profit": snapshot.unrealized_profit,
            "favorable_points": snapshot.favorable_points,
            "adverse_points": snapshot.adverse_points,
            "holding_seconds": snapshot.holding_seconds,
            "thesis_valid": snapshot.thesis_valid,
            "market_regime_valid": snapshot.market_regime_valid,
            "recommended_action": decision.recommended_action,
            "holding_reason": decision.holding_reason,
            "reason_codes": decision.reason_codes,
            "proposed_close_fraction": decision.proposed_close_fraction,
            "execution_permission": False,
            "lifecycle_financial_provenance": financials,
            "updated_at": decision.decided_at,
        }
        record.update(financials)
        record["read_model_checksum"] = _checksum(record)
        return record

    @classmethod
    def _financial_provenance(
        cls,
        *,
        snapshot: PositionCareSnapshot,
        decision: PositionCareDecision,
        point_size: float | None,
        trade_tick_size: float | None,
        trade_tick_value: float | None,
    ) -> dict[str, Any]:
        direction = snapshot.direction.upper()
        sign = 1.0 if direction == "BUY" else -1.0
        initial_risk_distance = max(0.0, sign * (snapshot.entry_price - snapshot.initial_stop_price))
        current_stop_delta = sign * (snapshot.current_stop_price - snapshot.entry_price)
        proposed_stop_delta = sign * (decision.proposed_stop_price - snapshot.entry_price)
        current_target_distance = max(0.0, sign * (snapshot.current_take_profit_price - snapshot.current_price))
        current_stop_distance = max(0.0, sign * (snapshot.current_price - snapshot.current_stop_price))
        target_from_entry_distance = max(0.0, sign * (snapshot.current_take_profit_price - snapshot.entry_price))

        current_remaining_risk_distance = max(0.0, -current_stop_delta)
        current_locked_profit_distance = max(0.0, current_stop_delta)
        proposed_remaining_risk_distance = max(0.0, -proposed_stop_delta)
        proposed_locked_profit_distance = max(0.0, proposed_stop_delta)

        def points(distance: float) -> float | None:
            try:
                size = float(point_size or 0.0)
            except (TypeError, ValueError):
                size = 0.0
            return round(distance / size, 2) if size > 0 else None

        def usd(distance: float) -> float | None:
            try:
                tick_size = float(trade_tick_size or 0.0)
                tick_value = float(trade_tick_value or 0.0)
                volume = float(snapshot.volume_lots or 0.0)
            except (TypeError, ValueError):
                return None
            if tick_size <= 0 or tick_value <= 0 or volume <= 0:
                return None
            return round(distance / tick_size * tick_value * volume, 2)

        initial_risk_usd = usd(initial_risk_distance)
        target_from_entry_usd = usd(target_from_entry_distance)
        planned_rr = (
            round(target_from_entry_usd / initial_risk_usd, 4)
            if initial_risk_usd not in (None, 0.0) and target_from_entry_usd is not None
            else None
        )
        return {
            "lifecycle_financial_status": (
                "AVAILABLE"
                if usd(1.0) is not None and points(1.0) is not None
                else "BROKER_METADATA_UNAVAILABLE"
            ),
            "initial_risk_points": points(initial_risk_distance),
            "initial_risk_usd": initial_risk_usd,
            "planned_reward_points": points(target_from_entry_distance),
            "planned_reward_usd": target_from_entry_usd,
            "planned_risk_reward_ratio": planned_rr,
            "current_distance_to_stop_points": points(current_stop_distance),
            "current_distance_to_stop_usd": usd(current_stop_distance),
            "current_distance_to_target_points": points(current_target_distance),
            "current_distance_to_target_usd": usd(current_target_distance),
            "remaining_risk_points": points(current_remaining_risk_distance),
            "remaining_risk_usd": usd(current_remaining_risk_distance),
            "locked_profit_points": points(current_locked_profit_distance),
            "locked_profit_usd": usd(current_locked_profit_distance),
            "proposed_remaining_risk_points": points(proposed_remaining_risk_distance),
            "proposed_remaining_risk_usd": usd(proposed_remaining_risk_distance),
            "proposed_locked_profit_points": points(proposed_locked_profit_distance),
            "proposed_locked_profit_usd": usd(proposed_locked_profit_distance),
            "maximum_favorable_excursion_points": float(snapshot.favorable_points),
            "maximum_favorable_excursion_usd": usd(max(0.0, float(snapshot.favorable_points)) * float(point_size or 0.0)),
            "maximum_adverse_excursion_points": float(snapshot.adverse_points),
            "maximum_adverse_excursion_usd": usd(max(0.0, float(snapshot.adverse_points)) * float(point_size or 0.0)),
            "unrealized_profit_usd": float(snapshot.unrealized_profit),
            "recommended_action": decision.recommended_action,
            "recommended_close_fraction": float(decision.proposed_close_fraction),
            "exit_reason_codes": decision.reason_codes,
        }


class PositionCareDashboardContract:
    @staticmethod
    def as_dict() -> dict[str, Any]:
        return {
            "operations_refresh_seconds": 5,
            "source_dataset": "position_care_dashboard_records",
            "required_actions": (
                "HOLD_POSITION", "HOLD_WITH_CAUTION", "RECOMMEND_BREAK_EVEN_UPDATE",
                "RECOMMEND_TRAILING_STOP_UPDATE", "RECOMMEND_PARTIAL_CLOSE",
                "RECOMMEND_FULL_CLOSE", "ENTER_SAFE_MODE",
            ),
            "execution_permission_locked_false": True,
            "show_holding_reason": True,
            "show_stop_change_reason": True,
            "show_close_reason": True,
        }
