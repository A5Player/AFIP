"""Milestone T Pack 11: complete trade-plan and capital stewardship foundation.

This module is deterministic and execution-neutral.  It certifies that a full
market, entry, capital, care, exit, and recovery plan exists before any later
runtime layer may consider a new order.  It never sends, modifies, or closes an
MT5 order.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from afip.historical_replay_research import AppendOnlyResearchDataset


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _checksum(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def _positive(value: float) -> bool:
    return float(value) > 0.0


@dataclass(frozen=True)
class MarketSituationPlan:
    regime: str
    pattern_name: str
    pattern_family: str
    structure_state: str
    volatility_state: str
    liquidity_state: str
    session: str
    news_state: str
    directional_bias: str
    situation_confidence: float
    invalidation_conditions: tuple[str, ...]


@dataclass(frozen=True)
class EntryPlan:
    direction: str
    entry_method: str
    entry_zone_low: float
    entry_zone_high: float
    confirmation_conditions: tuple[str, ...]
    cancellation_conditions: tuple[str, ...]
    chase_prohibited: bool
    maximum_signal_age_seconds: int
    requested_units: int
    maximum_units: int
    unit_spacing_points: float
    maximum_spread_points: float
    maximum_slippage_points: float


@dataclass(frozen=True)
class CapitalManagementPlan:
    profile_id: str
    base_lot: float
    capital_per_unit: float
    account_balance: float
    account_equity: float
    free_margin: float
    current_floating_drawdown_percent: float
    maximum_trade_risk_percent: float
    maximum_account_drawdown_percent: float
    daily_loss_limit_percent: float
    weekly_loss_limit_percent: float
    monthly_loss_limit_percent: float
    capital_capacity_units: int
    risk_capacity_units: int
    margin_capacity_units: int
    exposure_capacity_units: int
    correlation_capacity_units: int
    profile_capacity_units: int

    @property
    def allowed_units(self) -> int:
        capacities = (
            self.capital_capacity_units,
            self.risk_capacity_units,
            self.margin_capacity_units,
            self.exposure_capacity_units,
            self.correlation_capacity_units,
            self.profile_capacity_units,
        )
        return max(0, min(int(value) for value in capacities))


@dataclass(frozen=True)
class PositionCarePlan:
    holding_thesis: str
    thesis_validation_conditions: tuple[str, ...]
    thesis_failure_conditions: tuple[str, ...]
    break_even_trigger: str
    trailing_policy: str
    partial_close_policy: str
    add_position_policy: str
    maximum_holding_seconds: int
    overnight_policy: str
    weekend_policy: str
    news_management_policy: str


@dataclass(frozen=True)
class ExitPlan:
    initial_stop_price: float
    hard_invalidation_price: float
    target_prices: tuple[float, ...]
    structure_exit_conditions: tuple[str, ...]
    time_exit_condition: str
    thesis_failure_exit: str
    volatility_exit: str
    emergency_exit: str
    profit_protection_policy: str
    trailing_exit_policy: str


@dataclass(frozen=True)
class FailureRecoveryPlan:
    stale_data_action: str
    mt5_disconnect_action: str
    internet_disconnect_action: str
    restart_reconciliation_required: bool
    unknown_order_action: str
    state_corruption_action: str
    spread_anomaly_action: str
    broker_rejection_action: str
    manual_order_guard_action: str
    equity_anomaly_action: str
    safe_mode_action: str
    alert_required: bool


@dataclass(frozen=True)
class CompleteTradePlan:
    plan_id: str
    plan_version: str
    symbol: str
    ranking_id: str
    selected_standard_id: str
    market: MarketSituationPlan
    entry: EntryPlan
    capital: CapitalManagementPlan
    care: PositionCarePlan
    exit: ExitPlan
    recovery: FailureRecoveryPlan
    created_at: str = field(default_factory=_utc_now)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_units"] = self.capital.allowed_units
        payload["plan_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class TradePlanCertification:
    certification_id: str
    plan_id: str
    certified: bool
    status: str
    allowed_units: int
    requested_units: int
    rejection_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    rule: str
    certified_at: str
    plan_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TradePlanLifecycleEvent:
    event_id: str
    plan_id: str
    profile_id: str
    event_type: str
    reason_code: str
    explanation: str
    observed_at: str
    metadata: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CompleteTradePlanCertifier:
    """Apply NO_COMPLETE_PLAN_NO_ORDER and capital stewardship rules."""

    RULE = "NO_COMPLETE_PLAN_NO_ORDER"

    def __init__(self, dataset_root: str | Path | None = None) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root) if dataset_root is not None else None

    def certify(self, plan: CompleteTradePlan) -> TradePlanCertification:
        reasons: list[str] = []
        warnings: list[str] = []

        if not plan.plan_id.strip() or not plan.plan_version.strip():
            reasons.append("plan_identity_missing")
        if not plan.symbol.strip() or not plan.ranking_id.strip() or not plan.selected_standard_id.strip():
            reasons.append("plan_traceability_missing")

        market = plan.market
        if market.regime.upper() == "UNKNOWN" or market.pattern_name.upper() in {"", "UNKNOWN"}:
            reasons.append("market_situation_not_identified")
        if not market.invalidation_conditions:
            reasons.append("market_invalidation_conditions_missing")
        if not 0.0 <= market.situation_confidence <= 100.0:
            reasons.append("market_situation_confidence_invalid")

        entry = plan.entry
        if entry.direction.upper() not in {"BUY", "SELL"}:
            reasons.append("entry_direction_invalid")
        if entry.entry_zone_low > entry.entry_zone_high:
            reasons.append("entry_zone_invalid")
        if not entry.confirmation_conditions or not entry.cancellation_conditions:
            reasons.append("entry_conditions_incomplete")
        if not entry.chase_prohibited:
            warnings.append("entry_chase_prohibition_not_enabled")
        if entry.requested_units < 1 or entry.maximum_units < 1:
            reasons.append("entry_units_invalid")
        if entry.requested_units > entry.maximum_units:
            reasons.append("requested_units_above_plan_maximum")
        if entry.maximum_signal_age_seconds <= 0:
            reasons.append("signal_expiry_missing")
        if not _positive(entry.maximum_spread_points) or not _positive(entry.maximum_slippage_points):
            reasons.append("execution_cost_limits_missing")

        capital = plan.capital
        if capital.profile_id.upper() not in {"P1", "P2", "P3", "P4"}:
            reasons.append("profile_id_invalid")
        if not _positive(capital.base_lot) or not _positive(capital.capital_per_unit):
            reasons.append("capital_unit_policy_invalid")
        if capital.account_equity <= 0 or capital.free_margin < 0:
            reasons.append("account_capital_state_invalid")
        if capital.current_floating_drawdown_percent > capital.maximum_account_drawdown_percent:
            reasons.append("account_drawdown_limit_reached")
        if capital.allowed_units < 1:
            reasons.append("capital_capacity_unavailable")
        if entry.requested_units > capital.allowed_units:
            reasons.append("requested_units_above_capital_capacity")

        care = plan.care
        if not care.holding_thesis.strip():
            reasons.append("holding_thesis_missing")
        if not care.thesis_validation_conditions or not care.thesis_failure_conditions:
            reasons.append("position_care_conditions_incomplete")
        if care.maximum_holding_seconds <= 0:
            reasons.append("maximum_holding_time_missing")

        exit_plan = plan.exit
        if not _positive(exit_plan.initial_stop_price) or not _positive(exit_plan.hard_invalidation_price):
            reasons.append("protective_stop_missing")
        if not exit_plan.target_prices:
            reasons.append("profit_target_missing")
        if not exit_plan.structure_exit_conditions:
            reasons.append("structure_exit_conditions_missing")
        if not exit_plan.emergency_exit.strip() or not exit_plan.profit_protection_policy.strip():
            reasons.append("exit_protection_incomplete")

        recovery = plan.recovery
        required_actions = (
            recovery.stale_data_action, recovery.mt5_disconnect_action,
            recovery.internet_disconnect_action, recovery.unknown_order_action,
            recovery.state_corruption_action, recovery.spread_anomaly_action,
            recovery.broker_rejection_action, recovery.manual_order_guard_action,
            recovery.equity_anomaly_action, recovery.safe_mode_action,
        )
        if not recovery.restart_reconciliation_required:
            reasons.append("restart_reconciliation_not_required")
        if any(not value.strip() for value in required_actions):
            reasons.append("failure_recovery_actions_incomplete")
        if not recovery.alert_required:
            warnings.append("failure_alert_not_required")

        plan_payload = plan.as_dict()
        plan_checksum = str(plan_payload["plan_checksum"])
        certified = not reasons
        status = "CERTIFIED" if certified else "BLOCKED"
        certification_id = f"TPC-{plan_checksum[:16].upper()}"
        result = TradePlanCertification(
            certification_id=certification_id,
            plan_id=plan.plan_id,
            certified=certified,
            status=status,
            allowed_units=min(entry.requested_units, capital.allowed_units) if certified else 0,
            requested_units=entry.requested_units,
            rejection_reasons=tuple(sorted(set(reasons))),
            warnings=tuple(sorted(set(warnings))),
            rule=self.RULE,
            certified_at=_utc_now(),
            plan_checksum=plan_checksum,
        )
        if self.dataset is not None:
            self.dataset.append("complete_trade_plans", plan_payload)
            self.dataset.append("trade_plan_certifications", result.as_dict())
        return result


class TradePlanLifecycleRecorder:
    """Append auditable entry, care, exit, and recovery reasoning events."""

    ALLOWED_EVENT_TYPES = {
        "PLAN_CREATED", "PLAN_CERTIFIED", "ENTRY_WAIT", "ENTRY_BLOCKED",
        "ENTRY_APPROVED", "POSITION_OPENED", "POSITION_HELD", "BREAK_EVEN_MOVED",
        "TRAILING_STOP_MOVED", "PARTIAL_CLOSE", "POSITION_CLOSED",
        "SAFE_MODE_ENTERED", "RECOVERY_RECONCILED",
    }

    def __init__(self, dataset_root: str | Path) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root)

    def record(self, event: TradePlanLifecycleEvent) -> dict[str, Any]:
        if event.event_type not in self.ALLOWED_EVENT_TYPES:
            raise ValueError("unknown trade plan lifecycle event type")
        if not event.reason_code.strip() or not event.explanation.strip():
            raise ValueError("lifecycle event requires reason and explanation")
        return self.dataset.append("trade_plan_lifecycle_events", event.as_dict())


class TradePlanDashboardContract:
    """Stable read-model fields for Operations and Intelligence dashboards."""

    OPERATIONS_FIELDS = (
        "plan_id", "plan_version", "certification_status", "profile_id", "symbol",
        "regime", "pattern_name", "market_situation", "entry_reason", "waiting_reason",
        "blocked_reason", "requested_units", "allowed_units", "base_lot",
        "capital_per_unit", "account_balance", "account_equity", "free_margin",
        "floating_drawdown_percent", "holding_thesis", "holding_reason",
        "initial_stop_price", "current_stop_price", "target_prices", "break_even_policy",
        "trailing_policy", "close_reason", "recovery_state", "decision_trace_id",
    )
    INTELLIGENCE_FIELDS = (
        "ranking_id", "selected_standard_id", "plan_id", "plan_version", "pattern_name",
        "pattern_family", "regime", "situation_confidence", "capital_policy",
        "entry_policy", "care_policy", "exit_policy", "recovery_policy",
        "certification_rejection_reasons", "plan_checksum",
    )

    @classmethod
    def as_dict(cls) -> dict[str, Any]:
        return {
            "operations_refresh_seconds": 5,
            "operations_profiles": ("P1", "P2", "P3", "P4"),
            "operations_fields": cls.OPERATIONS_FIELDS,
            "intelligence_refresh": "MANUAL_ONLY",
            "intelligence_preserve_scroll_position": True,
            "intelligence_fields": cls.INTELLIGENCE_FIELDS,
        }
