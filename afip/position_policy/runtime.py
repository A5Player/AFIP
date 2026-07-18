"""Deterministic confidence-to-unit policy shared by simulation and gateways."""
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ConfidenceUnitDecision:
    confidence: float
    maximum_units: int
    policy_version: str = "AFIP_POSITION_POLICY_V1"
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
