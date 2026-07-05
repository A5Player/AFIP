"""Production Milestone B Pack 17 runtime for capital allocation controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.capital.capital_allocator import CapitalAllocator


@dataclass(frozen=True)
class ProductionMilestoneBCapitalRuntimeResult:
    """Integrated Pack 17 runtime result."""

    status: str
    capital_allocation_status: str
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


class ProductionMilestoneBCapitalRuntime:
    """Run capital allocation controls against portfolio equity and requests."""

    def __init__(self) -> None:
        self.capital_allocator = CapitalAllocator()

    def run(
        self,
        portfolio_equity: Mapping[str, object] | object,
        proposed_allocation: float,
        position_requests: Iterable[Mapping[str, object]],
        capital_policy: Mapping[str, object] | None = None,
    ) -> ProductionMilestoneBCapitalRuntimeResult:
        summary = self.capital_allocator.allocate(portfolio_equity, proposed_allocation, position_requests, capital_policy)
        return ProductionMilestoneBCapitalRuntimeResult(
            status="PRODUCTION_MILESTONE_B_CAPITAL_READY" if summary.approved else "PRODUCTION_MILESTONE_B_CAPITAL_REVIEW",
            capital_allocation_status=summary.status,
            reserve_status=summary.reserve_status,
            policy_status=summary.policy_status,
            distribution_status=summary.distribution_status,
            utilization_status=summary.utilization_status,
            approved=summary.approved,
            total_equity=summary.total_equity,
            reserve_amount=summary.reserve_amount,
            available_capital=summary.available_capital,
            proposed_allocation=summary.proposed_allocation,
            distributed_capital=summary.distributed_capital,
            allocation_ratio=summary.allocation_ratio,
            utilization_ratio=summary.utilization_ratio,
            failed_rules=summary.failed_rules,
            allocations=summary.allocations,
        )
