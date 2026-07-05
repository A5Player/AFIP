from afip.intelligence.decision_stability_index import DecisionStabilityIndex
from afip.intelligence.signal_persistence_analysis import SignalPersistenceAnalysis
from afip.learning.confidence_aggregation_refinement import ConfidenceAggregationRefinement
from afip.runtime.production_milestone_a_decision_trace_runtime import ProductionMilestoneADecisionTraceRuntime


def _recent_decisions(side="BUY", confidence=82, count=6):
    return [
        {
            "side": side,
            "confidence": confidence,
            "entry_score": confidence,
            "position_confidence": confidence,
        }
        for _ in range(count)
    ]


def _observations(side="BUY", strength=84, count=6):
    return [
        {
            "side": side,
            "direction": side,
            "strength": strength,
            "confidence": strength,
        }
        for _ in range(count)
    ]


def _context():
    return {
        "action": "BUY",
        "decision_state": {
            "side": "BUY",
            "recent_decisions": _recent_decisions(),
            "confidence_stability": 88,
            "regime_alignment": 82,
            "execution_alignment": 86,
        },
        "signal_state": {
            "side": "BUY",
            "observations": _observations(),
            "timeframe_confirmation": 86,
            "volatility_penalty": 8,
        },
        "confidence_state": {
            "entry_confidence": 84,
            "position_confidence": 82,
            "regime_confidence": 80,
            "learning_confidence": 78,
            "risk_adjustment": 92,
        },
    }


def test_a1_pack_10_decision_stability_index_ready_for_aligned_decisions():
    result = DecisionStabilityIndex().evaluate(_context()["decision_state"]).to_dict()

    assert result["status"] == "READY"
    assert result["production_ready"] is True
    assert result["stability_state"] in {"STANDARD_STABILITY", "HIGH_STABILITY"}
    assert result["blockers"] == []


def test_a1_pack_10_decision_stability_index_observes_directional_conflict():
    state = dict(_context()["decision_state"])
    state["recent_decisions"] = _recent_decisions(side="SELL", confidence=83, count=6)
    result = DecisionStabilityIndex().evaluate(state).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_ready"] is False
    assert "directional_alignment_below_decision_threshold" in result["blockers"]


def test_a2_pack_10_signal_persistence_analysis_ready_for_persistent_signal():
    result = SignalPersistenceAnalysis().evaluate(_context()["signal_state"]).to_dict()

    assert result["status"] == "READY"
    assert result["production_ready"] is True
    assert result["persistence_state"] in {"STANDARD_PERSISTENCE", "HIGH_PERSISTENCE"}
    assert result["blockers"] == []


def test_a2_pack_10_signal_persistence_analysis_observes_weak_timeframe_confirmation():
    state = dict(_context()["signal_state"])
    state["timeframe_confirmation"] = 35.0
    result = SignalPersistenceAnalysis().evaluate(state).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_ready"] is False
    assert "timeframe_confirmation_below_signal_threshold" in result["blockers"]


def test_a3_pack_10_confidence_aggregation_refinement_allows_high_quality_confidence():
    result = ConfidenceAggregationRefinement().evaluate(_context()["confidence_state"]).to_dict()

    assert result["status"] == "READY"
    assert result["optimization_allowed"] is True
    assert result["aggregation_state"] in {"STANDARD_CONFIDENCE", "HIGH_CONFIDENCE"}


def test_a3_pack_10_confidence_aggregation_refinement_observes_low_risk_adjustment():
    state = dict(_context()["confidence_state"])
    state["risk_adjustment"] = 30.0
    result = ConfidenceAggregationRefinement().evaluate(state).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["optimization_allowed"] is False
    assert "risk_adjustment_below_aggregation_threshold" in result["blockers"]


def test_a4_pack_10_decision_trace_runtime_allows_traceable_buy_action():
    result = ProductionMilestoneADecisionTraceRuntime().evaluate(_context()).to_dict()

    assert result["status"] == "READY"
    assert result["production_allowed"] is True
    assert result["action"] == "BUY"
    assert len(result["trace"]) == 4
    assert result["blockers"] == []


def test_a4_pack_10_decision_trace_runtime_observes_signal_persistence_issue():
    context = _context()
    context["signal_state"] = dict(context["signal_state"])
    context["signal_state"]["observations"] = _observations(side="SELL", strength=82, count=6)
    result = ProductionMilestoneADecisionTraceRuntime().evaluate(context).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_allowed"] is False
    assert result["action"] == "HOLD"
    assert any(item.startswith("signal_persistence:") for item in result["blockers"])
