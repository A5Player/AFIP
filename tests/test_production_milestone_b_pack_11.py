from afip.governance.execution_approval_policy import ExecutionApprovalPolicy
from afip.governance.order_submission_audit import OrderSubmissionAudit
from afip.governance.pre_trade_compliance import PreTradeCompliance
from afip.runtime.production_milestone_b_approval_runtime import ProductionMilestoneBApprovalRuntime


def _execution_plan():
    return {
        "action": "BUY",
        "readiness": "READY",
        "lot_size": 0.03,
        "exposure_ratio": 0.30,
    }


def _account_state():
    return {
        "margin_level": 850.0,
        "minimum_margin_level": 250.0,
        "daily_drawdown_ratio": 0.02,
        "maximum_daily_drawdown_ratio": 0.10,
        "maximum_exposure_ratio": 0.80,
    }


def _market_state():
    return {"spread_points": 24.0, "spread_limit": 35.0, "session_status": "OPEN"}


def test_pre_trade_compliance_approves_valid_execution_plan():
    result = PreTradeCompliance().evaluate(_execution_plan(), _account_state(), _market_state())
    assert result.status == "PRE_TRADE_COMPLIANCE_APPROVED"
    assert result.approved is True
    assert result.score == 100.0
    assert result.failed_rules == ()


def test_pre_trade_compliance_blocks_spread_and_margin_failures():
    account = {**_account_state(), "margin_level": 120.0}
    market = {**_market_state(), "spread_points": 46.0}
    result = PreTradeCompliance().evaluate(_execution_plan(), account, market)
    assert result.status == "PRE_TRADE_COMPLIANCE_REVIEW"
    assert result.approved is False
    assert "margin_level_below_limit" in result.failed_rules
    assert "spread_limit_exceeded" in result.failed_rules


def test_pre_trade_compliance_blocks_non_executable_action():
    result = PreTradeCompliance().evaluate({**_execution_plan(), "action": "WAIT"}, _account_state(), _market_state())
    assert result.approved is False
    assert "action_not_executable" in result.failed_rules


def test_execution_approval_policy_approves_compliant_high_confidence_decision():
    compliance = PreTradeCompliance().evaluate(_execution_plan(), _account_state(), _market_state())
    result = ExecutionApprovalPolicy().approve(compliance, {"action": "BUY", "confidence": 82})
    assert result.status == "EXECUTION_APPROVAL_READY"
    assert result.approval == "APPROVED"
    assert result.approved is True


def test_execution_approval_policy_rejects_failed_compliance():
    compliance = PreTradeCompliance().evaluate(_execution_plan(), _account_state(), {**_market_state(), "session_status": "CLOSED"})
    result = ExecutionApprovalPolicy().approve(compliance, {"action": "BUY", "confidence": 82})
    assert result.approval == "REJECTED"
    assert result.approved is False


def test_execution_approval_policy_keeps_low_confidence_conditional():
    compliance = PreTradeCompliance().evaluate(_execution_plan(), _account_state(), _market_state())
    result = ExecutionApprovalPolicy().approve(compliance, {"action": "BUY", "confidence": 54})
    assert result.status == "EXECUTION_APPROVAL_SELECTIVE"
    assert result.approval == "CONDITIONAL"
    assert result.approved is False


def test_order_submission_audit_creates_deterministic_identifier():
    compliance = PreTradeCompliance().evaluate(_execution_plan(), _account_state(), _market_state())
    record = OrderSubmissionAudit().create(_execution_plan(), compliance, sequence=11)
    assert record.status == "ORDER_SUBMISSION_AUDIT_READY"
    assert record.audit_id == "AFIP-ORDER-000011-APPROVED-BUY"
    assert record.approved is True


def test_production_milestone_b_approval_runtime_integrates_controls():
    result = ProductionMilestoneBApprovalRuntime().run(
        execution_plan=_execution_plan(),
        decision_profile={"action": "BUY", "confidence": 84},
        account_state=_account_state(),
        market_state=_market_state(),
        sequence=11,
    )
    assert result.status == "PRODUCTION_MILESTONE_B_APPROVAL_READY"
    assert result.approval == "APPROVED"
    assert result.audit_id == "AFIP-ORDER-000011-APPROVED-BUY"
    assert result.failed_rules == ()
