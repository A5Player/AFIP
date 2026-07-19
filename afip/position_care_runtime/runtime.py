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
        if snapshot.direction.upper() == "BUY":
            candidate = snapshot.entry_price + max(0.0, snapshot.favorable_points * 0.5)
            return max(snapshot.current_stop_price, candidate)
        candidate = snapshot.entry_price - max(0.0, snapshot.favorable_points * 0.5)
        if snapshot.current_stop_price <= 0:
            return candidate
        return min(snapshot.current_stop_price, candidate)


class PositionCareDashboardReadModelBuilder:
    def build(self, *, snapshot: PositionCareSnapshot, decision: PositionCareDecision) -> dict[str, Any]:
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
            "updated_at": decision.decided_at,
        }
        record["read_model_checksum"] = _checksum(record)
        return record


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
