"""Capital distribution builder for production position allocation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class CapitalDistributionResult:
    """Capital distribution across proposed position weights."""

    status: str
    proposed_allocation: float
    distributed_capital: float
    position_count: int
    allocations: tuple[dict[str, object], ...]
    ready: bool
    reason: str


class CapitalDistribution:
    """Distribute approved capital across weighted position requests."""

    def distribute(
        self,
        proposed_allocation: float,
        position_requests: Iterable[Mapping[str, object]],
    ) -> CapitalDistributionResult:
        requests = list(position_requests)
        allocation = round(max(0.0, float(proposed_allocation or 0.0)), 8)
        if allocation <= 0:
            return CapitalDistributionResult("CAPITAL_DISTRIBUTION_REVIEW", allocation, 0.0, len(requests), (), False, "allocation_not_positive")
        if not requests:
            return CapitalDistributionResult("CAPITAL_DISTRIBUTION_REVIEW", allocation, 0.0, 0, (), False, "position_requests_empty")
        weights = [max(0.0, self._number(request, "weight", 1.0)) for request in requests]
        total_weight = sum(weights)
        if total_weight <= 0:
            return CapitalDistributionResult("CAPITAL_DISTRIBUTION_REVIEW", allocation, 0.0, len(requests), (), False, "total_weight_not_positive")
        allocations: list[dict[str, object]] = []
        distributed = 0.0
        for request, weight in zip(requests, weights, strict=True):
            capital_amount = round(allocation * (weight / total_weight), 8)
            distributed = round(distributed + capital_amount, 8)
            allocations.append(
                {
                    "account_id": self._text(request, "account_id") or "ACCOUNT",
                    "symbol": self._text(request, "symbol") or "PORTFOLIO",
                    "weight": round(weight, 8),
                    "capital_amount": capital_amount,
                }
            )
        return CapitalDistributionResult(
            status="CAPITAL_DISTRIBUTION_READY",
            proposed_allocation=allocation,
            distributed_capital=distributed,
            position_count=len(allocations),
            allocations=tuple(allocations),
            ready=True,
            reason="capital_distribution_ready",
        )

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
