from afip.decision.decision_consensus_engine import DecisionConsensusEngine
from afip.decision.decision_confidence_model import DecisionConfidenceModel
from afip.decision.decision_priority_engine import DecisionPriorityEngine
from afip.decision.decision_risk_adjustment import DecisionRiskAdjustment
from afip.decision.decision_traceability import DecisionTraceability
from afip.runtime.production_milestone_b_decision_runtime import ProductionMilestoneBDecisionRuntime


def test_decision_consensus_engine_returns_buy_consensus():
    result = DecisionConsensusEngine().evaluate([
        {"action": "BUY", "confidence": 90, "weight": 0.4},
        {"action": "BUY", "confidence": 80, "weight": 0.3},
        {"action": "WAIT", "confidence": 40, "weight": 0.1},
    ])
    assert result.status == "DECISION_CONSENSUS_READY"
    assert result.action == "BUY"


def test_decision_consensus_engine_handles_empty_input():
    result = DecisionConsensusEngine().evaluate([])
    assert result.status == "DECISION_CONSENSUS_EMPTY"
    assert result.action == "NO_ACTION"


def test_decision_confidence_model_calculates_high_grade():
    result = DecisionConfidenceModel().calculate(90, 85, 80, 75, 70)
    assert result.status == "DECISION_CONFIDENCE_READY"
    assert result.grade == "HIGH"


def test_decision_priority_engine_ranks_high_priority():
    result = DecisionPriorityEngine().rank({"confidence": 88, "liquidity_score": 84, "volatility_score": 52, "risk_status": "ACCEPTABLE"})
    assert result.status == "DECISION_PRIORITY_READY"
    assert result.priority == "HIGH"


def test_decision_risk_adjustment_reduces_when_exposure_is_elevated():
    result = DecisionRiskAdjustment().adjust("BUY", 82, drawdown_ratio=0.03, exposure_ratio=0.75)
    assert result.action == "REDUCE"
    assert result.risk_status == "CAUTION"


def test_decision_risk_adjustment_blocks_when_drawdown_is_restricted():
    result = DecisionRiskAdjustment().adjust("SELL", 82, drawdown_ratio=0.30, exposure_ratio=0.20)
    assert result.action == "NO_ACTION"
    assert result.risk_status == "RESTRICTED"


def test_decision_traceability_creates_trace_identifier():
    result = DecisionTraceability().create({"action": "BUY", "confidence": 77.3, "reason": "test"}, sequence=12)
    assert result.status == "DECISION_TRACE_READY"
    assert result.trace_id == "AFIP-DECISION-000012-BUY"


def test_production_milestone_b_decision_runtime_integrates_components():
    result = ProductionMilestoneBDecisionRuntime().evaluate(
        [{"action": "BUY", "confidence": 90, "weight": 0.5}, {"action": "BUY", "confidence": 78, "weight": 0.3}],
        market_context={"context_score": 82, "execution_score": 80, "learning_score": 75, "memory_score": 74, "liquidity_score": 85},
        risk_context={"drawdown_ratio": 0.02, "exposure_ratio": 0.30},
    )
    assert result["status"] == "PRODUCTION_MILESTONE_B_DECISION_READY"
    assert result["action"] == "BUY"
    assert result["trace_id"].startswith("AFIP-DECISION-")
