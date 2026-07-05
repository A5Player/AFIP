"""Capital utilization analysis for production portfolio allocation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CapitalUtilizationResult:
    """Capital utilization summary after allocation."""

    status: str
    available_capital: float
    distributed_capital: float
    utilization_ratio: float
    maximum_utilization_ratio: float
    within_limit: bool
    reason: str


class CapitalUtilization:
    """Evaluate how much available capital is used by the allocation."""

    def evaluate(
        self,
        reserve_result: Mapping[str, object] | object,
        distribution_result: Mapping[str, object] | object,
        policy: Mapping[str, object] | None = None,
    ) -> CapitalUtilizationResult:
        policy = policy or {}
        reserve_status = self._text(reserve_result, "status")
        distribution_status = self._text(distribution_result, "status")
        available_capital = self._number(reserve_result, "available_capital")
        distributed_capital = self._number(distribution_result, "distributed_capital")
        maximum_ratio = self._number(policy, "maximum_utilization_ratio", 0.80)
        if reserve_status != "CAPITAL_RESERVE_READY":
            return CapitalUtilizationResult("CAPITAL_UTILIZATION_REVIEW", available_capital, distributed_capital, 0.0, maximum_ratio, False, "capital_reserve_not_ready")
        if distribution_status != "CAPITAL_DISTRIBUTION_READY":
            return CapitalUtilizationResult("CAPITAL_UTILIZATION_REVIEW", available_capital, distributed_capital, 0.0, maximum_ratio, False, "capital_distribution_not_ready")
        if available_capital <= 0:
            return CapitalUtilizationResult("CAPITAL_UTILIZATION_REVIEW", available_capital, distributed_capital, 0.0, maximum_ratio, False, "available_capital_not_positive")
        utilization_ratio = round(distributed_capital / available_capital, 8)
        if utilization_ratio > maximum_ratio:
            return CapitalUtilizationResult("CAPITAL_UTILIZATION_REVIEW", available_capital, distributed_capital, utilization_ratio, maximum_ratio, False, "utilization_ratio_above_limit")
        return CapitalUtilizationResult("CAPITAL_UTILIZATION_READY", available_capital, distributed_capital, utilization_ratio, maximum_ratio, True, "capital_utilization_ready")

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
