from afip.execution.broker_fill_assessment import BrokerFillAssessment
from afip.execution.order_lifecycle_record import OrderLifecycleRecordBuilder
from afip.execution.order_settlement import OrderSettlement
from afip.runtime.production_milestone_b_settlement_runtime import ProductionMilestoneBSettlementRuntime


def _approval_result():
    return {
        "approved": True,
        "audit_id": "AFIP-ORDER-000012-APPROVED-BUY",
        "reason": "execution_approved_for_order_submission",
    }


def _execution_plan():
    return {
        "account_id": "ACCOUNT_A",
        "symbol": "GOLD#",
        "action": "BUY",
        "lot_size": 0.03,
        "requested_price": 2365.10,
    }


def _broker_response():
    return {"status": "FILLED", "filled_quantity": 0.03, "fill_price": 2365.18}


def _settlement_limits():
    return {"minimum_fill_ratio": 1.0, "maximum_slippage_points": 15.0, "point_value": 0.01}


def test_order_lifecycle_record_builder_accepts_approved_order():
    record = OrderLifecycleRecordBuilder().build(_approval_result(), _execution_plan(), sequence=12)
    assert record.lifecycle_state == "ORDER_LIFECYCLE_ACCEPTED"
    assert record.order_id == "AFIP-ORDER-000012-APPROVED-BUY"
    assert record.approved is True
    assert record.requested_quantity == 0.03


def test_order_lifecycle_record_builder_routes_unapproved_order_to_review():
    record = OrderLifecycleRecordBuilder().build({"approved": False}, _execution_plan(), sequence=12)
    assert record.lifecycle_state == "ORDER_LIFECYCLE_REVIEW"
    assert record.approved is False


def test_broker_fill_assessment_accepts_valid_fill():
    record = OrderLifecycleRecordBuilder().build(_approval_result(), _execution_plan(), sequence=12)
    result = BrokerFillAssessment().evaluate(record, _broker_response(), _settlement_limits())
    assert result.status == "BROKER_FILL_ACCEPTED"
    assert result.accepted is True
    assert result.slippage_points == 8.0
    assert result.failed_rules == ()


def test_broker_fill_assessment_rejects_excessive_slippage():
    record = OrderLifecycleRecordBuilder().build(_approval_result(), _execution_plan(), sequence=12)
    response = {**_broker_response(), "fill_price": 2365.40}
    result = BrokerFillAssessment().evaluate(record, response, _settlement_limits())
    assert result.status == "BROKER_FILL_REVIEW"
    assert result.accepted is False
    assert "slippage_limit_exceeded" in result.failed_rules


def test_broker_fill_assessment_rejects_partial_fill_below_limit():
    record = OrderLifecycleRecordBuilder().build(_approval_result(), _execution_plan(), sequence=12)
    response = {**_broker_response(), "status": "PARTIAL_FILLED", "filled_quantity": 0.01}
    result = BrokerFillAssessment().evaluate(record, response, _settlement_limits())
    assert result.accepted is False
    assert "fill_ratio_below_limit" in result.failed_rules


def test_order_settlement_prepares_position_accounting_output():
    record = OrderLifecycleRecordBuilder().build(_approval_result(), _execution_plan(), sequence=12)
    fill = BrokerFillAssessment().evaluate(record, _broker_response(), _settlement_limits())
    result = OrderSettlement().settle(record, fill, sequence=12)
    assert result.status == "ORDER_SETTLEMENT_READY"
    assert result.settled is True
    assert result.position_quantity == 0.03
    assert result.notional_value == 70.9554


def test_order_settlement_uses_negative_quantity_for_sell_orders():
    plan = {**_execution_plan(), "action": "SELL"}
    approval = {**_approval_result(), "audit_id": "AFIP-ORDER-000012-APPROVED-SELL"}
    record = OrderLifecycleRecordBuilder().build(approval, plan, sequence=12)
    fill = BrokerFillAssessment().evaluate(record, _broker_response(), _settlement_limits())
    result = OrderSettlement().settle(record, fill, sequence=12)
    assert result.position_quantity == -0.03
    assert result.settled is True


def test_production_milestone_b_settlement_runtime_integrates_lifecycle_and_fill():
    result = ProductionMilestoneBSettlementRuntime().run(
        approval_result=_approval_result(),
        execution_plan=_execution_plan(),
        broker_response=_broker_response(),
        settlement_limits=_settlement_limits(),
        sequence=12,
    )
    assert result.status == "PRODUCTION_MILESTONE_B_SETTLEMENT_READY"
    assert result.settled is True
    assert result.fill_status == "BROKER_FILL_ACCEPTED"
    assert result.order_id == "AFIP-ORDER-000012-APPROVED-BUY"
    assert result.failed_rules == ()
