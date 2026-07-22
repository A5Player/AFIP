"""Phase U Pack 3.5 single lot and position-sizing authority.

The authority is deterministic and side-effect free.  Every consumer receives
one structured decision; consumers may reduce units for a later safety failure
but must never increase or recalculate the approved allocation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from afip.capital_growth_engine import CapitalGrowthEngine
from afip.position_capacity_formula import capital_tiers_from_profile
from afip.position_policy import requested_units_within_confidence_ceiling

BASE_LOT = 0.01
MAX_SIGNAL_UNITS = 3
POLICY_VERSION = "AFIP_LOT_AUTHORITY_MAXIMUM_LOT_SIZE_UNIT_V3"


@dataclass(frozen=True)
class LotAuthorityResult:
    profile_id: str
    balance: float
    equity: float
    base_lot: float
    requested_units: int
    confidence_units: int
    capital_units: int
    risk_units: int
    profile_max_units: int
    execution_safety_units: int
    approved_units: int
    approved_lot_per_order: float
    total_approved_lot: float
    limiting_gate: str
    reason: str
    policy_version: str
    calculated_at: str

    @property
    def approved_lots(self) -> tuple[float, ...]:
        return tuple(self.approved_lot_per_order for _ in range(self.approved_units))

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["approved_lots"] = self.approved_lots
        return data


def _integer(value: Any, default: int) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return max(0, default)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return max(0.0, default)


def calculate_lot_authority(
    *,
    profile: Mapping[str, Any],
    decision: Mapping[str, Any] | None,
    confidence: float,
    balance: float,
    equity: float | None = None,
    current_orders: int = 0,
    risk_units: int | None = None,
    execution_safety_units: int | None = None,
    calculated_at: str | None = None,
) -> LotAuthorityResult:
    """Return the sole approved lot allocation for execution/replay/dashboard."""
    mapping = decision if isinstance(decision, Mapping) else {}
    profile_id = str(profile.get("profile_id", mapping.get("profile_id", "UNKNOWN"))).upper()
    safe_balance = _number(balance)
    safe_equity = _number(equity if equity is not None else balance)
    available_capital = min(safe_balance, safe_equity) if safe_equity > 0 else safe_balance

    requested = requested_units_within_confidence_ceiling(mapping, confidence)
    profile_max = min(MAX_SIGNAL_UNITS, _integer(profile.get("maximum_units", MAX_SIGNAL_UNITS), MAX_SIGNAL_UNITS))
    if str(profile.get("allocation_mode", "")).upper() == "RESEARCH_FIXED_001" and not bool(profile.get("execution_enabled", False)):
        profile_max = 0

    maximum_orders = min(MAX_SIGNAL_UNITS, _integer(profile.get("maximum_concurrent_orders", profile_max), profile_max))
    current = _integer(current_orders, 0)
    allocation_mode = str(profile.get("allocation_mode", "")).upper()
    if allocation_mode not in {"CAPITAL_TIER_TABLE", "RESEARCH_FIXED_001"}:
        raise ValueError("obsolete_or_unknown_allocation_mode_forbidden")
    # Legacy capital-per-unit fields are accepted for backward-compatible reads only.
    # They are intentionally ignored and never participate in lot calculation.
    _legacy_capital_fields_ignored = (
        profile.get("capital_per_unit"),
        profile.get("capital_per_unit_legacy_only"),
    )
    del _legacy_capital_fields_ignored
    growth = CapitalGrowthEngine.evaluate(
        mode=allocation_mode,
        balance=available_capital,
        current_orders=current,
        capital_tiers=capital_tiers_from_profile(profile),
        maximum_orders=maximum_orders,
        legacy_capital_per_unit=0.0,
        legacy_maximum_units=0,
        lot_per_unit=BASE_LOT,
    )
    capital_units = min(MAX_SIGNAL_UNITS, len(growth.available_lots))
    # Capital Tier Table is the sole Maximum Lot Size authority for P1-P3.
    # P4 is explicitly capped by configuration at one 0.01-lot unit.
    approved_lot = float(growth.available_lots[0]) if growth.available_lots else BASE_LOT
    approved_lot = min(approved_lot, _number(profile.get("maximum_lot_per_order", approved_lot), approved_lot))
    safe_risk_units = min(MAX_SIGNAL_UNITS, _integer(risk_units, MAX_SIGNAL_UNITS))
    safe_execution_units = min(MAX_SIGNAL_UNITS, _integer(execution_safety_units, MAX_SIGNAL_UNITS))

    gates = {
        "REQUESTED": requested.requested_units,
        "CONFIDENCE": requested.confidence_maximum_units,
        "CAPITAL": capital_units,
        "RISK": safe_risk_units,
        "PROFILE_MAX": profile_max,
        "EXECUTION_SAFETY": safe_execution_units,
    }
    approved = min(gates.values()) if gates else 0
    priority = ("REQUESTED", "CONFIDENCE", "CAPITAL", "RISK", "PROFILE_MAX", "EXECUTION_SAFETY")
    limiting_gate = next(name for name in priority if gates[name] == approved)
    reasons = {
        "REQUESTED": "REQUEST_LIMITED",
        "CONFIDENCE": "CONFIDENCE_LIMITED",
        "CAPITAL": "CAPITAL_LIMITED",
        "RISK": "RISK_LIMITED",
        "PROFILE_MAX": "PROFILE_LIMITED",
        "EXECUTION_SAFETY": "EXECUTION_SAFETY_LIMITED",
    }
    timestamp = calculated_at or datetime.now(timezone.utc).isoformat()
    return LotAuthorityResult(
        profile_id=profile_id,
        balance=round(safe_balance, 2),
        equity=round(safe_equity, 2),
        base_lot=BASE_LOT,
        requested_units=requested.requested_units,
        confidence_units=requested.confidence_maximum_units,
        capital_units=capital_units,
        risk_units=safe_risk_units,
        profile_max_units=profile_max,
        execution_safety_units=safe_execution_units,
        approved_units=approved,
        approved_lot_per_order=round(approved_lot, 2),
        total_approved_lot=round(approved * approved_lot, 2),
        limiting_gate=limiting_gate,
        reason=reasons[limiting_gate],
        policy_version=POLICY_VERSION,
        calculated_at=timestamp,
    )
