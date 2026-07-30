import json
from pathlib import Path

from afip.opportunity_quality import (
    ELITE,
    ENTRY_ELIGIBLE,
    HIGH_QUALITY,
    WAIT,
    ELIGIBLE_FOR_ADAPTIVE_SL_REVIEW,
    NOT_ELIGIBLE,
    OQSComponent,
    OpportunityQualityEngine,
    PlanReviewInput,
)


def _review(score: float, **changes):
    base = dict(
        plan_id="plan-001",
        plan_status="ELIGIBLE_FOR_OQS_REVIEW",
        strategy_id="strategy-001",
        strategy_status="ELIGIBLE_FOR_PLAN_REVIEW",
        evidence_count=20,
        sample_size=100,
        all_authority_gates_passed=True,
        data_integrity_approved=True,
        components=(
            OQSComponent("market_structure", score, 0.20),
            OQSComponent("pattern_confidence", score, 0.15),
            OQSComponent("context_match", score, 0.15),
            OQSComponent("research_evidence", score, 0.10),
            OQSComponent("historical_similarity", score, 0.10),
            OQSComponent("market_regime", score, 0.10),
            OQSComponent("execution_quality", score, 0.05),
            OQSComponent("risk_quality", score, 0.05),
            OQSComponent("reward_risk", score, 0.05),
            OQSComponent("data_integrity", score, 0.05),
        ),
    )
    base.update(changes)
    return PlanReviewInput(**base)


def test_oqs_boundaries():
    engine = OpportunityQualityEngine()
    assert engine.assess(_review(96.99)).status == WAIT
    assert engine.assess(_review(97.00)).status == ENTRY_ELIGIBLE
    assert engine.assess(_review(98.00)).status == HIGH_QUALITY
    assert engine.assess(_review(99.00)).status == ELITE


def test_only_elite_can_proceed_to_adaptive_sl_review():
    engine = OpportunityQualityEngine()
    assert engine.assess(_review(98.99)).adaptive_sl_review_status == NOT_ELIGIBLE
    assert engine.assess(_review(99.00)).adaptive_sl_review_status == ELIGIBLE_FOR_ADAPTIVE_SL_REVIEW


def test_fail_closed_on_upstream_or_authority_failure():
    engine = OpportunityQualityEngine()
    assert engine.assess(_review(99.5, plan_status="WAIT")).status == WAIT
    assert engine.assess(_review(99.5, all_authority_gates_passed=False)).status == WAIT
    assert engine.assess(_review(99.5, data_integrity_approved=False)).status == WAIT


def test_fail_closed_on_evidence_and_component_authority():
    engine = OpportunityQualityEngine()
    assert engine.assess(_review(99.5, evidence_count=4)).reason == "insufficient_evidence_count"
    assert engine.assess(_review(99.5, sample_size=29)).reason == "insufficient_sample_size"
    blocked_components = (OQSComponent("data_integrity", 100, 1.0, authority_approved=False),)
    assert engine.assess(_review(99.5, components=blocked_components)).reason == "oqs_component_authority_not_approved"


def test_contract_and_no_execution_authority():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads((root / "config" / "opportunity_quality_runtime_contract.json").read_text(encoding="utf-8"))
    assert contract["fail_closed"] is True
    assert contract["elite_output"] == "ELIGIBLE_FOR_ADAPTIVE_SL_REVIEW"
    assessment = OpportunityQualityEngine().assess(_review(99.5))
    assert assessment.execution_authority is False
    assert assessment.order_send_called is False
