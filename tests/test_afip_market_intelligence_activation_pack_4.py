from afip.decision.decision_intelligence import DecisionIntelligence
from afip.decision.intelligence_activation import activation_for, build_activation_matrix
from afip.pipeline.modular_intelligence_pipeline import ModularIntelligencePipeline
from afip.demo_execution_gateway.runtime import DemoExecutionGateway


def _item(name, direction="BUY", confidence=80.0, status="READY", reason="test"):
    return {"name": name, "direction": direction, "confidence": confidence, "status": status, "reason": reason}


def _bullish_snapshot():
    return {
        "opens": [100.0, 100.2, 100.1, 100.0, 100.4, 101.0, 101.5, 102.0, 102.8, 103.4],
        "highs": [100.5, 100.6, 100.4, 100.8, 101.4, 101.9, 102.4, 103.1, 103.8, 104.5],
        "lows": [99.7, 99.9, 99.8, 99.6, 100.9, 101.2, 101.7, 102.2, 102.9, 103.5],
        "closes": [100.1, 100.0, 99.95, 100.6, 101.2, 101.7, 102.2, 102.9, 103.6, 104.2],
        "volumes": [100] * 10,
        "spread": 25.0,
    }


def test_context_and_placeholder_modules_do_not_cast_directional_votes():
    result = DecisionIntelligence().decide([
        _item("CorrelationIntelligence", "BUY", 100),
        _item("NewsRiskIntelligence", "BUY", 100),
        _item("PerformanceIntelligence", "BUY", 100),
        _item("LearningIntelligence", "BUY", 100),
    ])
    assert result["action"] == "WAIT"
    assert result["buy_score"] == 0.0
    assert all(not item["vote_eligible"] for item in result["neutral_intelligence"])


def test_smc_composite_is_evidence_but_not_a_duplicate_vote():
    result = DecisionIntelligence().decide([
        _item("FairValueGapIntelligence", "SELL", 92),
        _item("ImbalanceIntelligence", "SELL", 88),
        _item("OrderBlockIntelligence", "SELL", 90),
        _item("SmartMoneyConceptIntelligence", "BUY", 100),
    ])
    assert result["action"] == "SELL"
    smc = next(item for item in result["explain"] if item["name"] == "SmartMoneyConceptIntelligence")
    assert smc["decision_vote"] is False
    assert smc["confidence_contribution"] == 0.0
    assert result["conflict_resolution_reason"] == "weighted_sell_evidence_exceeded_buy_evidence"


def test_non_ready_detector_cannot_vote():
    result = DecisionIntelligence().decide([
        _item("LiquiditySweepIntelligence", "BUY", 99, status="LEARNING"),
        _item("MarketStructureIntelligence", "SELL", 80),
    ])
    assert result["action"] == "SELL"
    sweep = next(item for item in result["explain"] if item["name"] == "LiquiditySweepIntelligence")
    assert sweep["vote_eligible"] is False


def test_conflict_trace_explains_support_oppose_neutral_and_scenario():
    result = DecisionIntelligence().decide([
        _item("MarketStructureIntelligence", "BUY", 90),
        _item("FairValueGapIntelligence", "SELL", 70),
        _item("CorrelationIntelligence", "BUY", 100),
    ])
    assert result["action"] == "BUY"
    assert result["supporting_intelligence"]
    assert result["opposing_intelligence"]
    assert result["neutral_intelligence"]
    assert result["selected_scenario"] == "BUY_WEIGHTED_INTELLIGENCE"
    assert result["rejected_scenarios"] == ["SELL"]


def test_pipeline_exposes_complete_activation_matrix():
    result = ModularIntelligencePipeline().run(_bullish_snapshot())
    assert len(result["activation_matrix"]) == result["module_count"]
    by_name = {item["name"]: item for item in result["activation_matrix"]}
    assert by_name["MarketStructureIntelligence"]["decision_vote"] is True
    assert by_name["SmartMoneyConceptIntelligence"]["decision_vote"] is False
    assert by_name["ExecutionIntelligence"]["role"] == "EXECUTION_CONTEXT"


def test_activation_matrix_records_current_downstream_gaps_honestly():
    matrix = build_activation_matrix(["MarketStructureIntelligence"])
    item = matrix[0]
    assert item["decision_status"] == "CONNECTED_TO_DECISION"
    assert item["entry_status"] == "CONNECTED_TO_ENTRY"
    assert item["position_care_status"] == "NOT_CONNECTED"
    assert item["exit_status"] == "NOT_CONNECTED"


def test_execution_snapshot_includes_activation_and_conflict_trace():
    modular = ModularIntelligencePipeline().run(_bullish_snapshot())
    snapshot = DemoExecutionGateway._intelligence_snapshot({
        "modular_intelligence": modular,
        "decision": modular["decision"],
        "risk": {"allowed": True},
        "order": {"status": "NO_ORDER"},
    })
    assert snapshot["activation_matrix"]
    assert snapshot["decision"]["conflict_resolution_reason"]
    assert "INTELLIGENCE_ACTIVATION_MATRIX" in DemoExecutionGateway._decision_pipeline(snapshot)


def test_unknown_module_defaults_to_non_voting_context():
    activation = activation_for("UnknownFutureIntelligence")
    assert activation.decision_vote is False
    assert activation.role == "UNCLASSIFIED_CONTEXT"
