"""Capital allocation coordinator for production portfolio controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.capital.allocation_policy import AllocationPolicy
from afip.capital.capital_distribution import CapitalDistribution
from afip.capital.capital_reserve import CapitalReserve
from afip.capital.capital_utilization import CapitalUtilization


@dataclass(frozen=True)
class CapitalAllocationSummary:
    """Integrated capital allocation summary."""

    status: str
    reserve_status: str
    policy_status: str
    distribution_status: str
    utilization_status: str
    approved: bool
    total_equity: float
    reserve_amount: float
    available_capital: float
    proposed_allocation: float
    distributed_capital: float
    allocation_ratio: float
    utilization_ratio: float
    failed_rules: tuple[str, ...]
    allocations: tuple[dict[str, object], ...]


class CapitalAllocator:
    """Coordinate reserve, policy, distribution, and utilization controls."""

    def __init__(self) -> None:
        self.reserve = CapitalReserve()
        self.policy = AllocationPolicy()
        self.distribution = CapitalDistribution()
        self.utilization = CapitalUtilization()

    def allocate(
        self,
        portfolio_equity: Mapping[str, object] | object,
        proposed_allocation: float,
        position_requests: Iterable[Mapping[str, object]],
        policy: Mapping[str, object] | None = None,
    ) -> CapitalAllocationSummary:
        policy = policy or {}
        reserve_result = self.reserve.calculate(portfolio_equity, policy)
        policy_result = self.policy.evaluate(reserve_result, proposed_allocation, policy)
        distribution_result = self.distribution.distribute(policy_result.proposed_allocation if policy_result.approved else 0.0, position_requests)
        utilization_result = self.utilization.evaluate(reserve_result, distribution_result, policy)
        failed: list[str] = []
        if not reserve_result.ready:
            failed.append(reserve_result.reason)
        if not policy_result.approved:
            failed.append(policy_result.reason)
        if not distribution_result.ready:
            failed.append(distribution_result.reason)
        if not utilization_result.within_limit:
            failed.append(utilization_result.reason)
        approved = not failed
        return CapitalAllocationSummary(
            status="CAPITAL_ALLOCATION_READY" if approved else "CAPITAL_ALLOCATION_REVIEW",
            reserve_status=reserve_result.status,
            policy_status=policy_result.status,
            distribution_status=distribution_result.status,
            utilization_status=utilization_result.status,
            approved=approved,
            total_equity=reserve_result.total_equity,
            reserve_amount=reserve_result.reserve_amount,
            available_capital=reserve_result.available_capital,
            proposed_allocation=policy_result.proposed_allocation,
            distributed_capital=distribution_result.distributed_capital,
            allocation_ratio=policy_result.allocation_ratio,
            utilization_ratio=utilization_result.utilization_ratio,
            failed_rules=tuple(failed),
            allocations=distribution_result.allocations,
        )
