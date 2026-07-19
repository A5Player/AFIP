"""Milestone T Pack 14: unattended continuity and recovery supervision.

This module certifies runtime continuity after interruption or restart.  It is
execution-neutral: it records checkpoints, reconciliation decisions and
operations read models, but never imports MetaTrader5, sends an order, changes
an order, or closes a position.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afip.historical_replay_research import AppendOnlyResearchDataset


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _checksum(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RuntimeContinuityCheckpoint:
    checkpoint_id: str
    runtime_instance_id: str
    previous_runtime_instance_id: str
    profile_id: str
    symbol: str
    last_heartbeat_at: str
    current_heartbeat_at: str
    restart_detected: bool
    interruption_seconds: int
    mt5_connected: bool
    internet_connected: bool
    market_data_fresh: bool
    account_state_available: bool
    positions_reconciled: bool
    open_position_count: int
    ledger_position_count: int
    unknown_position_count: int
    missing_position_count: int
    pending_change_count: int
    manual_position_detected: bool
    equity_state_valid: bool
    drawdown_within_limit: bool
    append_only_chain_valid: bool
    duplicate_prevention_ready: bool
    safe_mode_active: bool
    observed_at: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checkpoint_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class RuntimeRecoveryDecision:
    decision_id: str
    checkpoint_id: str
    profile_id: str
    symbol: str
    continuity_status: str
    recommended_action: str
    reason_codes: tuple[str, ...]
    new_risk_allowed: bool
    position_care_allowed: bool
    reconciliation_required: bool
    operator_attention_required: bool
    execution_permission: bool
    decided_at: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["decision_checksum"] = _checksum(payload)
        return payload


class UnattendedContinuitySupervisor:
    """Certify continuity without granting order execution authority."""

    EXECUTION_PERMISSION = False

    def __init__(self, dataset_root: str | Path | None = None) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root) if dataset_root is not None else None

    def evaluate(self, checkpoint: RuntimeContinuityCheckpoint) -> RuntimeRecoveryDecision:
        reasons: list[str] = []
        action = "CONTINUE_SUPERVISION"
        status = "CONTINUITY_READY"
        new_risk_allowed = True
        position_care_allowed = True
        reconciliation_required = False
        operator_attention = False

        if checkpoint.safe_mode_active:
            reasons.append("safe_mode_already_active")
            action = "REMAIN_IN_SAFE_MODE"
            status = "BLOCKED"
            new_risk_allowed = False
        elif not checkpoint.append_only_chain_valid:
            reasons.append("append_only_chain_invalid")
            action = "ENTER_SAFE_MODE"
            status = "BLOCKED"
            new_risk_allowed = False
            position_care_allowed = False
            operator_attention = True
        elif not checkpoint.mt5_connected or not checkpoint.internet_connected:
            if not checkpoint.mt5_connected:
                reasons.append("mt5_connection_unavailable")
            if not checkpoint.internet_connected:
                reasons.append("internet_connection_unavailable")
            action = "PAUSE_AND_RECONNECT"
            status = "WAITING"
            new_risk_allowed = False
            position_care_allowed = False
            reconciliation_required = True
        elif not checkpoint.account_state_available or not checkpoint.market_data_fresh:
            if not checkpoint.account_state_available:
                reasons.append("account_state_unavailable")
            if not checkpoint.market_data_fresh:
                reasons.append("market_data_stale")
            action = "PAUSE_AND_REFRESH_STATE"
            status = "WAITING"
            new_risk_allowed = False
            position_care_allowed = False
            reconciliation_required = True
        elif checkpoint.manual_position_detected:
            reasons.append("manual_position_detected")
            action = "ENTER_SAFE_MODE"
            status = "BLOCKED"
            new_risk_allowed = False
            operator_attention = True
        elif checkpoint.unknown_position_count > 0 or checkpoint.missing_position_count > 0:
            if checkpoint.unknown_position_count > 0:
                reasons.append("unknown_positions_present")
            if checkpoint.missing_position_count > 0:
                reasons.append("ledger_positions_missing_from_account")
            action = "RECONCILE_POSITIONS"
            status = "BLOCKED"
            new_risk_allowed = False
            position_care_allowed = False
            reconciliation_required = True
            operator_attention = True
        elif checkpoint.open_position_count != checkpoint.ledger_position_count or not checkpoint.positions_reconciled:
            reasons.append("position_count_not_reconciled")
            action = "RECONCILE_POSITIONS"
            status = "WAITING"
            new_risk_allowed = False
            position_care_allowed = False
            reconciliation_required = True
        elif checkpoint.pending_change_count > 0:
            reasons.append("pending_position_changes_require_reconciliation")
            action = "RECONCILE_PENDING_CHANGES"
            status = "WAITING"
            new_risk_allowed = False
            reconciliation_required = True
        elif not checkpoint.equity_state_valid or not checkpoint.drawdown_within_limit:
            if not checkpoint.equity_state_valid:
                reasons.append("equity_state_invalid")
            if not checkpoint.drawdown_within_limit:
                reasons.append("drawdown_limit_exceeded")
            action = "ENTER_SAFE_MODE"
            status = "BLOCKED"
            new_risk_allowed = False
            operator_attention = True
        elif not checkpoint.duplicate_prevention_ready:
            reasons.append("duplicate_prevention_not_ready")
            action = "PAUSE_NEW_RISK"
            status = "WAITING"
            new_risk_allowed = False
        elif checkpoint.restart_detected:
            reasons.append("restart_reconciled")
            action = "RESUME_SUPERVISION_AFTER_RESTART"
        elif checkpoint.interruption_seconds > 0:
            reasons.append("interruption_reconciled")
            action = "RESUME_SUPERVISION_AFTER_INTERRUPTION"
        else:
            reasons.append("runtime_continuity_confirmed")

        identity = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "profile_id": checkpoint.profile_id,
            "action": action,
            "reasons": tuple(reasons),
        }
        decision = RuntimeRecoveryDecision(
            decision_id=f"RCD-{_checksum(identity)[:16].upper()}",
            checkpoint_id=checkpoint.checkpoint_id,
            profile_id=checkpoint.profile_id,
            symbol=checkpoint.symbol,
            continuity_status=status,
            recommended_action=action,
            reason_codes=tuple(reasons),
            new_risk_allowed=new_risk_allowed,
            position_care_allowed=position_care_allowed,
            reconciliation_required=reconciliation_required,
            operator_attention_required=operator_attention,
            execution_permission=self.EXECUTION_PERMISSION,
            decided_at=_utc_now(),
        )
        if self.dataset is not None:
            self.dataset.append("runtime_continuity_checkpoints", checkpoint.as_dict())
            self.dataset.append("runtime_recovery_decisions", decision.as_dict())
        return decision


class ContinuityDashboardReadModelBuilder:
    def build(self, *, checkpoint: RuntimeContinuityCheckpoint, decision: RuntimeRecoveryDecision) -> dict[str, Any]:
        record = {
            "profile_id": checkpoint.profile_id,
            "symbol": checkpoint.symbol,
            "runtime_instance_id": checkpoint.runtime_instance_id,
            "restart_detected": checkpoint.restart_detected,
            "interruption_seconds": checkpoint.interruption_seconds,
            "mt5_connected": checkpoint.mt5_connected,
            "internet_connected": checkpoint.internet_connected,
            "market_data_fresh": checkpoint.market_data_fresh,
            "positions_reconciled": checkpoint.positions_reconciled,
            "open_position_count": checkpoint.open_position_count,
            "ledger_position_count": checkpoint.ledger_position_count,
            "unknown_position_count": checkpoint.unknown_position_count,
            "missing_position_count": checkpoint.missing_position_count,
            "pending_change_count": checkpoint.pending_change_count,
            "manual_position_detected": checkpoint.manual_position_detected,
            "continuity_status": decision.continuity_status,
            "recommended_action": decision.recommended_action,
            "reason_codes": decision.reason_codes,
            "new_risk_allowed": decision.new_risk_allowed,
            "position_care_allowed": decision.position_care_allowed,
            "reconciliation_required": decision.reconciliation_required,
            "operator_attention_required": decision.operator_attention_required,
            "execution_permission": False,
            "updated_at": decision.decided_at,
        }
        record["read_model_checksum"] = _checksum(record)
        return record


class UnattendedContinuityContract:
    @staticmethod
    def as_dict() -> dict[str, Any]:
        return {
            "operations_refresh_seconds": 5,
            "heartbeat_required": True,
            "restart_requires_reconciliation": True,
            "unknown_position_requires_safe_state": True,
            "manual_position_requires_safe_state": True,
            "new_risk_requires_continuity_ready": True,
            "execution_permission_locked_false": True,
            "source_datasets": (
                "runtime_continuity_checkpoints",
                "runtime_recovery_decisions",
                "continuity_dashboard_records",
            ),
        }
