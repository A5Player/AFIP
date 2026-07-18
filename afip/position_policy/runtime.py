"""Deterministic confidence-to-unit policy shared by simulation and gateways."""
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ConfidenceUnitDecision:
    confidence: float
    maximum_units: int
    policy_version: str = "AFIP_POSITION_POLICY_V2"
    reason: str = ""


def confidence_maximum_units(confidence: float) -> ConfidenceUnitDecision:
    """Return the certified maximum unit count for a confidence value.

    This is a capacity ceiling only. Capital, profile, risk, margin, trading-cost,
    duplicate-signal and execution-safety gates may reduce the final allocation.
    """
    try:
        value = float(confidence)
    except (TypeError, ValueError):
        value = 0.0
    if not math.isfinite(value):
        value = 0.0
    value = min(100.0, max(0.0, value))

    if value < 98.0:
        units = 0
        reason = "confidence_below_98"
    elif value < 98.5:
        units = 1
        reason = "confidence_98_to_98_49"
    elif value < 99.5:
        units = 2
        reason = "confidence_98_5_to_99_49"
    else:
        units = 3
        reason = "confidence_99_5_to_100"
    return ConfidenceUnitDecision(confidence=value, maximum_units=units, reason=reason)


@dataclass(frozen=True)
class RequestedUnitDecision:
    confidence: float
    confidence_maximum_units: int
    requested_units: int
    approved_units: int
    source: str
    policy_version: str = "AFIP_POSITION_POLICY_V2"
    reason: str = ""


def requested_units_within_confidence_ceiling(decision: object, confidence: float) -> RequestedUnitDecision:
    """Resolve an intelligence request without treating a ceiling as a target.

    Confidence only limits the maximum number of units.  The intelligence layer
    may explicitly request fewer units through one of the certified fields.  If
    no explicit request exists, AFIP defaults conservatively to one unit for an
    otherwise eligible signal; it never expands automatically to the ceiling.
    """
    ceiling = confidence_maximum_units(confidence)
    if ceiling.maximum_units <= 0:
        return RequestedUnitDecision(
            confidence=ceiling.confidence,
            confidence_maximum_units=0,
            requested_units=0,
            approved_units=0,
            source="CONFIDENCE_BLOCK",
            reason="confidence_below_unit_threshold",
        )

    mapping = decision if isinstance(decision, dict) else {}
    source = "CONSERVATIVE_DEFAULT_ONE_UNIT"
    requested = 1
    for key in ("requested_units", "recommended_units", "approved_units", "unit_count"):
        if key not in mapping:
            continue
        try:
            candidate = int(mapping.get(key, 0) or 0)
        except (TypeError, ValueError):
            candidate = 0
        if candidate > 0:
            requested = candidate
            source = f"INTELLIGENCE_{key.upper()}"
            break

    approved = min(max(0, requested), ceiling.maximum_units)
    reason = "requested_units_within_confidence_ceiling"
    if requested > ceiling.maximum_units:
        reason = "requested_units_reduced_by_confidence_ceiling"
    return RequestedUnitDecision(
        confidence=ceiling.confidence,
        confidence_maximum_units=ceiling.maximum_units,
        requested_units=requested,
        approved_units=approved,
        source=source,
        reason=reason,
    )
