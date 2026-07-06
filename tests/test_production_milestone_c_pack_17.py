from __future__ import annotations

from afip.decision_enhancement import (
    DecisionContextBuilder,
    DecisionEnhancementRuntime,
    DecisionEvidence,
    DecisionEvidenceAggregator,
    DecisionSelectionPolicy,
)
from afip.runtime.production_milestone_c_decision_enhancement_runtime import run_dict, sample_decision_evidence, sample_regime_classification


def _evidence(direction: str = "buy", *, cost: float = 22.0, confidence: float = 82.0) -> DecisionEvidence:
    return DecisionEvidence(
        market_regime="expansion",
        volatility_bucket="high",
        direction=direction,
        source="test_profile",
        confidence=confidence,
        expectancy=8.0,
        execution_cost_points=cost,
        reliability=84.0,
    )


def test_decision_evidence_normalizes_regime_first_key_before_signal() -> None:
    evidence = _evidence("bullish")
    assert evidence.direction == "BUY"
    assert evidence.regime_first_key == "EXPANSION|HIGH|BUY"


def test_decision_context_requires_market_regime_before_decision() -> None:
    context = DecisionContextBuilder().build(None)
    assert context.status == "DECISION_CONTEXT_DATA_REQUIRED"
    assert "market_regime_classification_required_before_decision" in context.reasons


def test_decision_context_accepts_ready_market_regime_state() -> None:
    context = DecisionContextBuilder().build(sample_regime_classification())
    assert context.status == "DECISION_CONTEXT_READY"
    assert context.regime_first_key == "EXPANSION|HIGH|BUY"


def test_decision_evidence_aggregator_filters_active_regime_before_direction() -> None:
    context = DecisionContextBuilder().build(sample_regime_classification())
    groups = DecisionEvidenceAggregator().aggregate(context, sample_decision_evidence())
    assert groups[0].regime_first_key == "EXPANSION|HIGH|BUY"
    assert all(group.regime_first_key.startswith("EXPANSION|HIGH|") for group in groups)


def test_decision_evidence_group_uses_data_derived_metrics() -> None:
    context = DecisionContextBuilder().build(sample_regime_classification())
    groups = DecisionEvidenceAggregator().aggregate(context, [_evidence(), _evidence(confidence=78.0)])
    group = groups[0]
    assert group.observations == 2
    assert group.average_confidence == 80.0
    assert group.average_execution_cost_points == 22.0
    assert group.evidence_score > 60.0


def test_decision_policy_waits_for_sufficient_evidence() -> None:
    context = DecisionContextBuilder().build(sample_regime_classification())
    groups = DecisionEvidenceAggregator().aggregate(context, [_evidence()])
    candidate = DecisionSelectionPolicy().select(groups)
    assert candidate.action == "WAIT"
    assert "decision_group_failed_policy" in candidate.reasons


def test_decision_policy_blocks_high_execution_cost() -> None:
    context = DecisionContextBuilder().build(sample_regime_classification())
    groups = DecisionEvidenceAggregator().aggregate(context, [_evidence(cost=55.0), _evidence(cost=54.0)])
    candidate = DecisionSelectionPolicy().select(groups)
    assert candidate.action == "WAIT"
    assert "decision_group_failed_policy" in candidate.reasons


def test_decision_policy_selects_data_derived_candidate() -> None:
    context = DecisionContextBuilder().build(sample_regime_classification())
    groups = DecisionEvidenceAggregator().aggregate(context, sample_decision_evidence())
    candidate = DecisionSelectionPolicy().select(groups)
    assert candidate.action == "BUY"
    assert candidate.score > 60.0
    assert "decision_policy_selected_data_derived_candidate" in candidate.reasons


def test_decision_enhancement_runtime_builds_ready_state() -> None:
    state = DecisionEnhancementRuntime().run(sample_regime_classification(), sample_decision_evidence())
    assert state.status == "DECISION_INTELLIGENCE_READY"
    assert state.decision["action"] == "BUY"
    assert state.context["status"] == "DECISION_CONTEXT_READY"


def test_decision_enhancement_runtime_handles_missing_regime() -> None:
    state = DecisionEnhancementRuntime().run(None, sample_decision_evidence())
    assert state.status == "DECISION_CONTEXT_DATA_REQUIRED"
    assert state.decision["action"] == "WAIT"


def test_production_milestone_c_decision_enhancement_runtime_is_deterministic() -> None:
    first = run_dict()
    second = run_dict()
    assert first == second
    assert first["status"] == "DECISION_INTELLIGENCE_READY"
