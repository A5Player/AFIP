from __future__ import annotations

from afip.decision.decision_action import DecisionAction
from afip.decision.decision_confidence import DecisionConfidence
from afip.decision.decision_reasoning import DecisionReasoning
from afip.decision.unified_decision_engine import UnifiedDecisionEngine
from afip.runtime.production_milestone_b_decision_runtime import ProductionMilestoneBDecisionRuntime


def test_unified_decision_engine_accepts_buy_alignment() -> None:
    result = UnifiedDecisionEngine().decide(
        fusion_profile={"direction": "BUY", "confidence": 0.88},
        weight_profile={"adaptive_score": 0.86},
        conflict_profile={"reconciled_direction": "BUY", "consensus_level": "HIGH", "consensus_score": 0.84, "conflict_ratio": 0.08},
        risk_profile={"risk_accepted": True, "execution_quality": "ACCEPTABLE"},
        supporting_factors=["trend", "liquidity", "momentum"],
    )
    assert result.status == "UNIFIED_DECISION_READY"
    assert result.action == "BUY"
    assert result.confidence >= 0.80


def test_unified_decision_engine_accepts_sell_alignment() -> None:
    result = UnifiedDecisionEngine().decide(
        fusion_profile={"direction": "SELL", "confidence": 0.90},
        weight_profile={"adaptive_score": 0.87},
        conflict_profile={"reconciled_direction": "SELL", "consensus_level": "HIGH", "consensus_score": 0.86, "conflict_ratio": 0.06},
        risk_profile={"allowed": True, "execution_quality": "ACCEPTABLE"},
    )
    assert result.action == "SELL"
    assert result.consensus_level == "HIGH"


def test_unified_decision_engine_waits_on_low_consensus() -> None:
    result = UnifiedDecisionEngine().decide(
        fusion_profile={"direction": "BUY", "confidence": 0.62},
        weight_profile={"adaptive_score": 0.58},
        conflict_profile={"reconciled_direction": "BUY", "consensus_level": "LOW", "consensus_score": 0.44, "conflict_ratio": 0.45},
        risk_profile={"risk_accepted": True},
    )
    assert result.action == "WAIT"
    assert result.execution_status == "REVIEW"


def test_unified_decision_engine_returns_no_action_when_risk_not_accepted() -> None:
    result = UnifiedDecisionEngine().decide(
        fusion_profile={"direction": "BUY", "confidence": 0.92},
        weight_profile={"adaptive_score": 0.90},
        conflict_profile={"reconciled_direction": "BUY", "consensus_level": "HIGH", "consensus_score": 0.90, "conflict_ratio": 0.02},
        risk_profile={"risk_accepted": False},
    )
    assert result.action == "NO_ACTION"
    assert result.risk_status == "NOT_ACCEPTED"


def test_decision_confidence_calculates_high_level() -> None:
    result = DecisionConfidence().calculate(0.90, 0.86, 0.84, 0.05, True)
    assert result.status == "DECISION_CONFIDENCE_READY"
    assert result.confidence_level == "HIGH"


def test_decision_action_reduces_for_execution_quality() -> None:
    result = DecisionAction().select("BUY", 0.76, "HIGH", True, "CAUTION")
    assert result.action == "REDUCE"
    assert result.execution_status == "SELECTIVE"


def test_decision_reasoning_explains_supporting_factors() -> None:
    result = DecisionReasoning().explain("BUY", "BUY", "HIGH", "HIGH", ["trend", "liquidity"], True)
    assert result.status == "DECISION_REASONING_READY"
    assert "trend+liquidity" in result.explanation


def test_decision_runtime_uses_default_profiles() -> None:
    result = ProductionMilestoneBDecisionRuntime().run()
    assert result.status == "MILESTONE_B_DECISION_RUNTIME_READY"
    assert result.action == "BUY"
    assert result.confidence_level in {"HIGH", "MODERATE"}
