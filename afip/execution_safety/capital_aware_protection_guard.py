from __future__ import annotations

from dataclasses import asdict, dataclass
from math import floor, isfinite
from typing import Any, Mapping


@dataclass(frozen=True)
class AllocationInput:
    available_capital: float
    free_margin: float
    capital_per_unit: float
    maximum_units: int
    confidence_units: int
    risk_units: int
    margin_units: int
    existing_exposure_units: int = 0
    allocation_mode: str = "LEGACY_FIXED_UNIT"
    capital_capacity_override: int | None = None


@dataclass(frozen=True)
class AllocationResult:
    allowed: bool
    allocated_units: int
    capital_capacity: int
    remaining_profile_capacity: int
    reason: str
    trace: Mapping[str, Any]


@dataclass(frozen=True)
class ProtectionPlan:
    entry_price: float
    stop_loss_price: float | None
    take_profit_price: float | None
    point_size: float
    side: str
    sl_source: str = ""
    tp_source: str = ""
    planned_horizon: str = ""
    minimum_reward_risk: float = 1.0


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str
    allocated_units: int
    allocation: Mapping[str, Any]
    protection: Mapping[str, Any]


def _finite_positive(value: float) -> bool:
    return isfinite(float(value)) and float(value) > 0.0


def allocate_units(data: AllocationInput) -> AllocationResult:
    """Allocate units fail-closed.

    maximum_units is a ceiling, never a target.
    The final number is the minimum capacity approved by every gate.
    """
    maximum_units = max(0, int(data.maximum_units))
    exposure = max(0, int(data.existing_exposure_units))
    remaining_profile_capacity = max(0, maximum_units - exposure)

    allocation_mode = str(data.allocation_mode).strip().upper()
    available_capital = max(0.0, min(float(data.available_capital), float(data.free_margin)))

    if allocation_mode == "CAPITAL_TIER_TABLE":
        if data.capital_capacity_override is None:
            return AllocationResult(
                False, 0, 0, remaining_profile_capacity,
                "capital_tier_capacity_missing",
                {"input": asdict(data)},
            )
        capital_capacity = max(0, int(data.capital_capacity_override))
    else:
        if not _finite_positive(data.capital_per_unit):
            return AllocationResult(
                False, 0, 0, remaining_profile_capacity,
                "invalid_capital_per_unit",
                {"input": asdict(data)},
            )
        capital_capacity = max(0, floor(available_capital / float(data.capital_per_unit)))

    capacities = {
        "capital_capacity": capital_capacity,
        "confidence_capacity": max(0, int(data.confidence_units)),
        "risk_capacity": max(0, int(data.risk_units)),
        "margin_capacity": max(0, int(data.margin_units)),
        "remaining_profile_capacity": remaining_profile_capacity,
    }
    allocated_units = min(capacities.values()) if capacities else 0

    reason = "capital_aware_units_approved" if allocated_units > 0 else "unit_capacity_unavailable"
    return AllocationResult(
        allowed=allocated_units > 0,
        allocated_units=allocated_units,
        capital_capacity=capital_capacity,
        remaining_profile_capacity=remaining_profile_capacity,
        reason=reason,
        trace={
            "input": asdict(data),
            "capacities": capacities,
            "final_allocated_units": allocated_units,
            "maximum_units_semantics": "CEILING_NOT_TARGET",
        },
    )


def validate_protection_plan(plan: ProtectionPlan) -> tuple[bool, str, Mapping[str, Any]]:
    side = str(plan.side).strip().upper()
    trace: dict[str, Any] = asdict(plan)

    if side not in {"BUY", "SELL"}:
        return False, "invalid_side", trace
    if not _finite_positive(plan.entry_price) or not _finite_positive(plan.point_size):
        return False, "invalid_market_price_or_point", trace
    if plan.stop_loss_price is None or plan.take_profit_price is None:
        return False, "protection_plan_unavailable", trace
    if not _finite_positive(plan.stop_loss_price) or not _finite_positive(plan.take_profit_price):
        return False, "invalid_protection_price", trace
    if not str(plan.sl_source).strip() or not str(plan.tp_source).strip():
        return False, "protection_source_missing", trace
    if not str(plan.planned_horizon).strip():
        return False, "planned_horizon_missing", trace

    if side == "BUY":
        risk_distance = plan.entry_price - plan.stop_loss_price
        reward_distance = plan.take_profit_price - plan.entry_price
    else:
        risk_distance = plan.stop_loss_price - plan.entry_price
        reward_distance = plan.entry_price - plan.take_profit_price

    if risk_distance <= 0:
        return False, "stop_loss_wrong_side", trace
    if reward_distance <= 0:
        return False, "take_profit_wrong_side", trace

    sl_points = risk_distance / plan.point_size
    tp_points = reward_distance / plan.point_size
    reward_risk = reward_distance / risk_distance

    trace.update({
        "sl_points": sl_points,
        "tp_points": tp_points,
        "reward_risk_ratio": reward_risk,
    })

    # Explicitly reject the observed legacy fixed fallback.
    if abs(sl_points - 3000.0) < 1e-9 and abs(tp_points - 500.0) < 1e-9:
        return False, "legacy_fixed_sl_tp_fallback_rejected", trace

    if reward_risk < float(plan.minimum_reward_risk):
        return False, "minimum_reward_risk_not_met", trace

    return True, "adaptive_protection_approved", trace


def approve_execution(
    allocation_input: AllocationInput,
    protection_plan: ProtectionPlan,
) -> SafetyDecision:
    allocation = allocate_units(allocation_input)
    protection_allowed, protection_reason, protection_trace = validate_protection_plan(protection_plan)

    if not allocation.allowed:
        return SafetyDecision(
            False,
            allocation.reason,
            0,
            allocation.trace,
            protection_trace,
        )

    if not protection_allowed:
        return SafetyDecision(
            False,
            protection_reason,
            0,
            allocation.trace,
            protection_trace,
        )

    return SafetyDecision(
        True,
        "capital_and_protection_approved",
        allocation.allocated_units,
        allocation.trace,
        protection_trace,
    )
