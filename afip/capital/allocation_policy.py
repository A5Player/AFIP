"""Capital allocation policy validation for production portfolio controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class AllocationPolicyResult:
    """Allocation policy evaluation for a proposed capital amount."""

    status: str
    proposed_allocation: float
    available_capital: float
    allocation_ratio: float
    maximum_allocation_ratio: float
    approved: bool
    reason: str


class AllocationPolicy:
    """Validate proposed capital allocation against available capital."""

    def evaluate(
        self,
        reserve_result: Mapping[str, object] | object,
        proposed_allocation: float,
        policy: Mapping[str, object] | None = None,
    ) -> AllocationPolicyResult:
        policy = policy or {}
        reserve_status = self._text(reserve_result, "status")
        available_capital = self._number(reserve_result, "available_capital")
        maximum_ratio = self._number(policy, "maximum_allocation_ratio", 0.50)
        allocation = round(max(0.0, float(proposed_allocation or 0.0)), 8)
        if reserve_status != "CAPITAL_RESERVE_READY":
            return AllocationPolicyResult("ALLOCATION_POLICY_REVIEW", allocation, available_capital, 0.0, maximum_ratio, False, "capital_reserve_not_ready")
        if available_capital <= 0:
            return AllocationPolicyResult("ALLOCATION_POLICY_REVIEW", allocation, available_capital, 0.0, maximum_ratio, False, "available_capital_not_positive")
        allocation_ratio = round(allocation / available_capital, 8)
        if allocation_ratio > maximum_ratio:
            return AllocationPolicyResult("ALLOCATION_POLICY_REVIEW", allocation, available_capital, allocation_ratio, maximum_ratio, False, "allocation_ratio_above_limit")
        return AllocationPolicyResult("ALLOCATION_POLICY_READY", allocation, available_capital, allocation_ratio, maximum_ratio, True, "allocation_policy_ready")

    @staticmethod
    def _number(value: Mapping[str, object] | object, key: str, default: float = 0.0) -> float:
        raw = value.get(key, default) if isinstance(value, Mapping) else getattr(value, key, default)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _text(value: Mapping[str, object] | object, key: str) -> str:
        raw = value.get(key, "") if isinstance(value, Mapping) else getattr(value, key, "")
        return str(raw)
