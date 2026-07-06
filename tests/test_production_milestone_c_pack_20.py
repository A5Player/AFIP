from afip.milestone_c_completion import (
    MilestoneCapabilityEvidence,
    MilestoneCompletionPolicy,
    MilestoneCompletionRegistry,
    MilestoneCompletionRuntime,
)
from afip.runtime.production_milestone_c_completion_runtime import run_dict, sample_completion_evidence


def test_completion_evidence_normalizes_financial_capability_key():
    evidence = MilestoneCapabilityEvidence(
        pack_id=17,
        capability_name="Decision Intelligence Enhancement",
        status="pass",
        quality_status="ready",
        sequence_order=17,
        dependency="market_regime_intelligence",
        runtime_entrypoint="production_milestone_c_decision_enhancement_runtime",
    )

    assert evidence.status == "COMPLETE"
    assert evidence.quality_status == "PASS"
    assert evidence.dependency == "MARKET_REGIME_INTELLIGENCE"
    assert evidence.completion_key == "PACK_17|17|DECISION INTELLIGENCE ENHANCEMENT"
    assert evidence.is_complete is True


def test_completion_registry_orders_capabilities_deterministically():
    values = list(reversed(sample_completion_evidence()))
    registry = MilestoneCompletionRegistry.build(values)

    assert registry.ordered_pack_ids == (13, 14, 15, 16, 17, 18, 19)
    assert registry.completion_ratio == 1.0


def test_completion_registry_reports_missing_required_pack():
    values = [item for item in sample_completion_evidence() if item.pack_id != 18]
    registry = MilestoneCompletionRegistry.build(values)

    assert registry.missing_pack_ids == (18,)
    assert registry.completion_ratio == 0.8571


def test_completion_registry_tracks_quality_failures():
    values = sample_completion_evidence()
    failed = MilestoneCapabilityEvidence(
        pack_id=19,
        capability_name="Production Integration",
        status="COMPLETE",
        quality_status="FAIL",
        sequence_order=19,
        dependency="EXECUTION_READINESS",
        runtime_entrypoint="production_milestone_c_production_integration_runtime",
    )
    values = [item for item in values if item.pack_id != 19] + [failed]
    registry = MilestoneCompletionRegistry.build(values)

    assert registry.failed_capability_keys == ("PACK_19|19|PRODUCTION INTEGRATION",)


def test_completion_registry_requires_regime_decision_execution_sequence():
    registry = MilestoneCompletionRegistry.build(sample_completion_evidence())

    assert registry.dependency_sequence_ready is True


def test_completion_policy_waits_when_pack_missing():
    values = [item for item in sample_completion_evidence() if item.pack_id != 16]
    decision = MilestoneCompletionPolicy().decide(MilestoneCompletionRegistry.build(values))

    assert decision.status == "MILESTONE_C_INCOMPLETE"
    assert decision.readiness == "WAIT"
    assert decision.reasons == ("required_milestone_c_pack_missing",)


def test_completion_policy_blocks_failed_quality_evidence():
    values = sample_completion_evidence()
    failed = MilestoneCapabilityEvidence(18, "Execution Readiness", "COMPLETE", "FAIL", 18, "DECISION_INTELLIGENCE", "runtime")
    values = [item for item in values if item.pack_id != 18] + [failed]
    decision = MilestoneCompletionPolicy().decide(MilestoneCompletionRegistry.build(values))

    assert decision.status == "MILESTONE_C_QUALITY_BLOCKED"
    assert decision.readiness == "BLOCKED"


def test_completion_policy_confirms_milestone_c_complete():
    decision = MilestoneCompletionPolicy().decide(MilestoneCompletionRegistry.build(sample_completion_evidence()))

    assert decision.status == "MILESTONE_C_COMPLETE"
    assert decision.readiness == "READY"
    assert decision.completion_ratio == 1.0


def test_completion_runtime_builds_final_audit_report():
    report = MilestoneCompletionRuntime().run(sample_completion_evidence()).as_dict()

    assert report["status"] == "MILESTONE_C_COMPLETE"
    assert report["audit"]["market_regime_before_decision"] is True
    assert report["audit"]["execution_readiness_before_production"] is True
    assert report["audit"]["deterministic_completion_report"] is True


def test_completion_runtime_handles_empty_evidence():
    report = MilestoneCompletionRuntime().run([]).as_dict()

    assert report["status"] == "MILESTONE_C_INCOMPLETE"
    assert report["decision"]["readiness"] == "WAIT"
    assert report["registry"]["missing_pack_ids"] == [13, 14, 15, 16, 17, 18, 19]


def test_production_milestone_c_completion_runtime_is_deterministic():
    first = run_dict()
    second = run_dict()

    assert first == second
    assert first["status"] == "MILESTONE_C_COMPLETE"
    assert first["reason"] == "milestone_c_completion_confirmed"
