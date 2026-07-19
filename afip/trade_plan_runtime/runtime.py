"""Milestone T Pack 12: certified plan runtime orchestration.

This module links research ranking, complete trade-plan certification, capital
capacity snapshots, recovery reconciliation, decision traces, and dashboard
read models.  It is execution-neutral: it never imports MetaTrader5, never
calls order_send, and never grants live execution permission.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afip.complete_trade_plan import CompleteTradePlan, TradePlanCertification
from afip.historical_replay_research import AppendOnlyResearchDataset


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _checksum(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CapitalCapacitySnapshot:
    snapshot_id: str
    profile_id: str
    symbol: str
    account_balance: float
    account_equity: float
    free_margin: float
    floating_drawdown_percent: float
    requested_units: int
    plan_capacity_units: int
    capital_capacity_units: int
    risk_capacity_units: int
    margin_capacity_units: int
    exposure_capacity_units: int
    correlation_capacity_units: int
    profile_capacity_units: int
    observed_at: str

    @property
    def allowed_units(self) -> int:
        capacities = (
            self.plan_capacity_units,
            self.capital_capacity_units,
            self.risk_capacity_units,
            self.margin_capacity_units,
            self.exposure_capacity_units,
            self.correlation_capacity_units,
            self.profile_capacity_units,
        )
        return max(0, min(self.requested_units, *(int(value) for value in capacities)))

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_units"] = self.allowed_units
        payload["snapshot_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class RecoveryReconciliationSnapshot:
    reconciliation_id: str
    profile_id: str
    mt5_connected: bool
    internet_connected: bool
    market_data_fresh: bool
    runtime_state_valid: bool
    account_state_reconciled: bool
    open_positions_reconciled: bool
    unknown_orders_present: bool
    manual_order_guard_clear: bool
    equity_state_valid: bool
    safe_mode_active: bool
    observed_at: str

    @property
    def ready_for_new_risk(self) -> bool:
        return all((
            self.mt5_connected,
            self.internet_connected,
            self.market_data_fresh,
            self.runtime_state_valid,
            self.account_state_reconciled,
            self.open_positions_reconciled,
            not self.unknown_orders_present,
            self.manual_order_guard_clear,
            self.equity_state_valid,
            not self.safe_mode_active,
        ))

    @property
    def blocking_reasons(self) -> tuple[str, ...]:
        checks = (
            (self.mt5_connected, "mt5_not_connected"),
            (self.internet_connected, "internet_not_connected"),
            (self.market_data_fresh, "market_data_stale"),
            (self.runtime_state_valid, "runtime_state_invalid"),
            (self.account_state_reconciled, "account_state_not_reconciled"),
            (self.open_positions_reconciled, "open_positions_not_reconciled"),
            (not self.unknown_orders_present, "unknown_orders_present"),
            (self.manual_order_guard_clear, "manual_order_guard_active"),
            (self.equity_state_valid, "equity_state_invalid"),
            (not self.safe_mode_active, "safe_mode_active"),
        )
        return tuple(reason for passed, reason in checks if not passed)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ready_for_new_risk"] = self.ready_for_new_risk
        payload["blocking_reasons"] = self.blocking_reasons
        payload["reconciliation_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class CertifiedPlanRuntimeDecision:
    decision_id: str
    profile_id: str
    symbol: str
    ranking_id: str
    plan_id: str
    certification_id: str
    capital_snapshot_id: str
    reconciliation_id: str
    status: str
    action: str
    requested_units: int
    allowed_units: int
    lot_per_unit: float
    reason_codes: tuple[str, ...]
    explanation: str
    execution_permission: bool
    decided_at: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["decision_checksum"] = _checksum(payload)
        return payload


class CertifiedTradePlanRuntimeCoordinator:
    """Coordinate certified evidence without creating execution authority."""

    EXECUTION_PERMISSION = False

    def __init__(self, dataset_root: str | Path | None = None) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root) if dataset_root is not None else None

    def decide(
        self,
        *,
        plan: CompleteTradePlan,
        certification: TradePlanCertification,
        capital_snapshot: CapitalCapacitySnapshot,
        reconciliation: RecoveryReconciliationSnapshot,
        ranking_eligible: bool,
    ) -> CertifiedPlanRuntimeDecision:
        reasons: list[str] = []
        if not ranking_eligible:
            reasons.append("ranking_not_eligible")
        if plan.ranking_id.strip() == "":
            reasons.append("ranking_trace_missing")
        if certification.plan_id != plan.plan_id or certification.plan_checksum != plan.as_dict()["plan_checksum"]:
            reasons.append("certification_plan_mismatch")
        if not certification.certified:
            reasons.extend(certification.rejection_reasons or ("trade_plan_not_certified",))
        if capital_snapshot.profile_id.upper() != plan.capital.profile_id.upper():
            reasons.append("capital_snapshot_profile_mismatch")
        if capital_snapshot.symbol.upper() != plan.symbol.upper():
            reasons.append("capital_snapshot_symbol_mismatch")
        if capital_snapshot.allowed_units < 1:
            reasons.append("runtime_capital_capacity_unavailable")
        if capital_snapshot.allowed_units < certification.allowed_units:
            reasons.append("runtime_capacity_below_certified_units")
        if not reconciliation.ready_for_new_risk:
            reasons.extend(reconciliation.blocking_reasons)

        eligible = not reasons
        status = "READY_FOR_EXECUTION_GATE_REVIEW" if eligible else "BLOCKED"
        action = plan.entry.direction.upper() if eligible else "NO_ORDER"
        allowed_units = min(certification.allowed_units, capital_snapshot.allowed_units) if eligible else 0
        explanation = (
            "Certified plan, ranking, capital capacity, and recovery reconciliation passed. "
            "Execution remains denied until existing external execution gates approve."
            if eligible else
            "New risk blocked because one or more certified-plan runtime prerequisites failed."
        )
        identity = {
            "profile_id": plan.capital.profile_id,
            "symbol": plan.symbol,
            "plan_id": plan.plan_id,
            "certification_id": certification.certification_id,
            "capital_snapshot_id": capital_snapshot.snapshot_id,
            "reconciliation_id": reconciliation.reconciliation_id,
            "status": status,
            "reason_codes": tuple(sorted(set(reasons))),
        }
        decision = CertifiedPlanRuntimeDecision(
            decision_id=f"CPRD-{_checksum(identity)[:16].upper()}",
            profile_id=plan.capital.profile_id,
            symbol=plan.symbol,
            ranking_id=plan.ranking_id,
            plan_id=plan.plan_id,
            certification_id=certification.certification_id,
            capital_snapshot_id=capital_snapshot.snapshot_id,
            reconciliation_id=reconciliation.reconciliation_id,
            status=status,
            action=action,
            requested_units=plan.entry.requested_units,
            allowed_units=allowed_units,
            lot_per_unit=plan.capital.base_lot,
            reason_codes=tuple(sorted(set(reasons))),
            explanation=explanation,
            execution_permission=self.EXECUTION_PERMISSION,
            decided_at=_utc_now(),
        )
        if self.dataset is not None:
            self.dataset.append("capital_capacity_snapshots", capital_snapshot.as_dict())
            self.dataset.append("recovery_reconciliations", reconciliation.as_dict())
            self.dataset.append("certified_plan_runtime_decisions", decision.as_dict())
        return decision


class ProfileOperationsReadModelBuilder:
    """Build stable P1-P4 Operations Dashboard records from certified decisions."""

    def build(
        self,
        *,
        plan: CompleteTradePlan,
        certification: TradePlanCertification,
        capital_snapshot: CapitalCapacitySnapshot,
        reconciliation: RecoveryReconciliationSnapshot,
        decision: CertifiedPlanRuntimeDecision,
        runtime_values: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        values = dict(runtime_values or {})
        record = {
            "profile_id": plan.capital.profile_id,
            "symbol": plan.symbol,
            "plan_id": plan.plan_id,
            "plan_version": plan.plan_version,
            "ranking_id": plan.ranking_id,
            "selected_standard_id": plan.selected_standard_id,
            "certification_status": certification.status,
            "runtime_decision_status": decision.status,
            "execution_permission": False,
            "market_regime": plan.market.regime,
            "pattern_name": plan.market.pattern_name,
            "pattern_family": plan.market.pattern_family,
            "entry_direction": plan.entry.direction,
            "entry_method": plan.entry.entry_method,
            "requested_units": plan.entry.requested_units,
            "certified_units": certification.allowed_units,
            "runtime_allowed_units": decision.allowed_units,
            "base_lot": plan.capital.base_lot,
            "capital_per_unit": plan.capital.capital_per_unit,
            "account_balance": capital_snapshot.account_balance,
            "account_equity": capital_snapshot.account_equity,
            "free_margin": capital_snapshot.free_margin,
            "floating_drawdown_percent": capital_snapshot.floating_drawdown_percent,
            "holding_thesis": plan.care.holding_thesis,
            "break_even_policy": plan.care.break_even_trigger,
            "trailing_policy": plan.care.trailing_policy,
            "initial_stop_price": plan.exit.initial_stop_price,
            "target_prices": plan.exit.target_prices,
            "recovery_ready": reconciliation.ready_for_new_risk,
            "recovery_blocking_reasons": reconciliation.blocking_reasons,
            "waiting_reason": values.get("waiting_reason", ""),
            "blocked_reason": ",".join(decision.reason_codes),
            "holding_reason": values.get("holding_reason", ""),
            "close_reason": values.get("close_reason", ""),
            "current_stop_price": values.get("current_stop_price", plan.exit.initial_stop_price),
            "current_take_profit_price": values.get("current_take_profit_price", plan.exit.target_prices[0]),
            "active_order_count": int(values.get("active_order_count", 0)),
            "updated_at": str(values.get("updated_at", _utc_now())),
        }
        record["read_model_checksum"] = _checksum(record)
        return record


class TradePlanRuntimeDashboardContract:
    @staticmethod
    def as_dict() -> dict[str, Any]:
        return {
            "operations_profiles": ("P1", "P2", "P3", "P4"),
            "operations_refresh_seconds": 5,
            "operations_source_dataset": "profile_operations_read_models",
            "intelligence_refresh": "MANUAL_ONLY",
            "intelligence_preserve_scroll_position": True,
            "intelligence_trace_chain": (
                "ranking_id", "selected_standard_id", "plan_id", "certification_id",
                "capital_snapshot_id", "reconciliation_id", "decision_id",
            ),
            "execution_permission_field_locked_false": True,
        }
