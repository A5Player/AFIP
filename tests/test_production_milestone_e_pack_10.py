from afip.milestone_e_completion import (
    MilestoneECapabilityEvidence,
    MilestoneECompletionPolicy,
    MilestoneECompletionRegistry,
    MilestoneECompletionRuntime,
)
from afip.runtime.production_milestone_e_completion_runtime import run_dict, sample_completion_evidence


def test_milestone_e_completion_evidence_normalizes_financial_capability_key():
    evidence = MilestoneECapabilityEvidence(
        pack_id=9,
        capability_name="Adaptive Learning",
        status="pass",
        quality_status="ready",
        sequence_order=9,
        dependency="macro_context",
        runtime_entrypoint="production_milestone_e_adaptive_learning_runtime",
    )

    assert evidence.status == "COMPLETE"
    assert evidence.quality_status == "PASS"
    assert evidence.dependency == "MACRO_CONTEXT"
    assert evidence.completion_key == "PACK_E9|9|ADAPTIVE LEARNING"
    assert evidence.is_complete is True


def test_milestone_e_completion_registry_orders_capabilities_deterministically():
    values = list(reversed(sample_completion_evidence()))
    registry = MilestoneECompletionRegistry.build(values)

    assert registry.ordered_pack_ids == (1, 2, 3, 4, 5, 6, 7, 8, 9)
    assert registry.completion_ratio == 1.0


def test_milestone_e_completion_registry_reports_missing_required_pack():
    values = [item for item in sample_completion_evidence() if item.pack_id != 8]
    registry = MilestoneECompletionRegistry.build(values)

    assert registry.missing_pack_ids == (8,)
    assert registry.completion_ratio == 0.8889


def test_milestone_e_completion_registry_tracks_quality_failures():
    values = sample_completion_evidence()
    failed = MilestoneECapabilityEvidence(
        pack_id=7,
        capability_name="Portfolio Intelligence",
        status="COMPLETE",
        quality_status="FAIL",
        sequence_order=7,
        dependency="PERFORMANCE_ATTRIBUTION",
        runtime_entrypoint="production_milestone_e_portfolio_intelligence_runtime",
    )
    values = [item for item in values if item.pack_id != 7] + [failed]
    registry = MilestoneECompletionRegistry.build(values)

    assert registry.failed_capability_keys == ("PACK_E7|7|PORTFOLIO INTELLIGENCE",)


def test_milestone_e_completion_registry_requires_intelligence_sequence():
    registry = MilestoneECompletionRegistry.build(sample_completion_evidence())

    assert registry.intelligence_sequence_ready is True
    assert registry.knowledge_first_ready is True


def test_milestone_e_completion_policy_waits_when_pack_missing():
    values = [item for item in sample_completion_evidence() if item.pack_id != 5]
    decision = MilestoneECompletionPolicy().decide(MilestoneECompletionRegistry.build(values))

    assert decision.status == "MILESTONE_E_INCOMPLETE"
    assert decision.readiness == "WAIT"
    assert decision.reasons == ("required_milestone_e_pack_missing",)


def test_milestone_e_completion_policy_blocks_failed_quality_evidence():
    values = sample_completion_evidence()
    failed = MilestoneECapabilityEvidence(6, "Performance Attribution", "COMPLETE", "FAIL", 6, "DYNAMIC_WEIGHT_ENGINE", "runtime")
    values = [item for item in values if item.pack_id != 6] + [failed]
    decision = MilestoneECompletionPolicy().decide(MilestoneECompletionRegistry.build(values))

    assert decision.status == "MILESTONE_E_QUALITY_BLOCKED"
    assert decision.readiness == "BLOCKED"


def test_milestone_e_completion_policy_confirms_milestone_e_complete():
    decision = MilestoneECompletionPolicy().decide(MilestoneECompletionRegistry.build(sample_completion_evidence()))

    assert decision.status == "MILESTONE_E_COMPLETE"
    assert decision.readiness == "READY"
    assert decision.completion_ratio == 1.0


def test_milestone_e_completion_runtime_builds_final_audit_report():
    report = MilestoneECompletionRuntime().run(sample_completion_evidence()).as_dict()

    assert report["status"] == "MILESTONE_E_COMPLETE"
    assert report["audit"]["session_intelligence_ready"] is True
    assert report["audit"]["macro_context_ready"] is True
    assert report["audit"]["adaptive_learning_ready"] is True
    assert report["audit"]["deterministic_completion_report"] is True


def test_milestone_e_completion_runtime_handles_empty_evidence():
    report = MilestoneECompletionRuntime().run([]).as_dict()

    assert report["status"] == "MILESTONE_E_INCOMPLETE"
    assert report["decision"]["readiness"] == "WAIT"
    assert report["registry"]["missing_pack_ids"] == [1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_production_milestone_e_completion_runtime_is_deterministic():
    first = run_dict()
    second = run_dict()

    assert first == second
    assert first["status"] == "MILESTONE_E_COMPLETE"
    assert first["reason"] == "milestone_e_completion_confirmed"
