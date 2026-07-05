"""Production Milestone B Pack 12 order settlement runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from afip.execution.broker_fill_assessment import BrokerFillAssessment
from afip.execution.order_lifecycle_record import OrderLifecycleRecordBuilder
from afip.execution.order_settlement import OrderSettlement


@dataclass(frozen=True)
class ProductionMilestoneBSettlementRuntimeResult:
    """Runtime output for order lifecycle settlement."""

    status: str
    settled: bool
    order_id: str
    settlement_id: str
    fill_status: str
    position_quantity: float
    average_price: float
    notional_value: float
    slippage_points: float
    failed_rules: tuple[str, ...]
    reason: str


class ProductionMilestoneBSettlementRuntime:
    """Run order lifecycle, broker fill assessment and settlement."""

    def run(
        self,
        approval_result: Mapping[str, object] | object | None = None,
        execution_plan: Mapping[str, object] | None = None,
        broker_response: Mapping[str, object] | None = None,
        settlement_limits: Mapping[str, object] | None = None,
        sequence: int = 1,
    ) -> ProductionMilestoneBSettlementRuntimeResult:
        lifecycle = OrderLifecycleRecordBuilder().build(approval_result, execution_plan, sequence=sequence)
        fill = BrokerFillAssessment().evaluate(lifecycle, broker_response, settlement_limits)
        settlement = OrderSettlement().settle(lifecycle, fill, sequence=sequence)
        status = "PRODUCTION_MILESTONE_B_SETTLEMENT_READY" if settlement.settled else "PRODUCTION_MILESTONE_B_SETTLEMENT_REVIEW"
        return ProductionMilestoneBSettlementRuntimeResult(
            status=status,
            settled=settlement.settled,
            order_id=lifecycle.order_id,
            settlement_id=settlement.settlement_id,
            fill_status=fill.status,
            position_quantity=settlement.position_quantity,
            average_price=settlement.average_price,
            notional_value=settlement.notional_value,
            slippage_points=fill.slippage_points,
            failed_rules=fill.failed_rules,
            reason=settlement.reason,
        )

    def run_dict(
        self,
        approval_result: Mapping[str, object] | object | None = None,
        execution_plan: Mapping[str, object] | None = None,
        broker_response: Mapping[str, object] | None = None,
        settlement_limits: Mapping[str, object] | None = None,
        sequence: int = 1,
    ) -> dict[str, object]:
        return asdict(self.run(approval_result, execution_plan, broker_response, settlement_limits, sequence))
