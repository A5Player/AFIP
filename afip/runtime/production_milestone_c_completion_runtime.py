"""Production entrypoint for Milestone C Pack 20 final completion."""

from __future__ import annotations

from afip.milestone_c_completion import MilestoneCapabilityEvidence, MilestoneCompletionRuntime


def sample_completion_evidence() -> list[MilestoneCapabilityEvidence]:
    values = [
        (13, "Adaptive Parameter Foundation", "COMPLETE", "PASS", 13, "ROOT", "production_milestone_c_adaptive_parameter_runtime"),
        (14, "Research Platform", "COMPLETE", "PASS", 14, "ADAPTIVE_PARAMETER_FOUNDATION", "production_milestone_c_research_platform_runtime"),
        (15, "Learning Foundation", "COMPLETE", "PASS", 15, "RESEARCH_PLATFORM", "production_milestone_c_learning_foundation_runtime"),
        (16, "Market Regime Intelligence", "COMPLETE", "PASS", 16, "LEARNING_FOUNDATION", "production_milestone_c_market_regime_runtime"),
        (17, "Decision Intelligence Enhancement", "COMPLETE", "PASS", 17, "MARKET_REGIME_INTELLIGENCE", "production_milestone_c_decision_enhancement_runtime"),
        (18, "Execution Readiness", "COMPLETE", "PASS", 18, "DECISION_INTELLIGENCE", "production_milestone_c_execution_readiness_runtime"),
        (19, "Production Integration", "COMPLETE", "PASS", 19, "EXECUTION_READINESS", "production_milestone_c_production_integration_runtime"),
    ]
    return [
        MilestoneCapabilityEvidence(
            pack_id=pack_id,
            capability_name=capability,
            status=status,
            quality_status=quality,
            sequence_order=order,
            dependency=dependency,
            runtime_entrypoint=runtime_entrypoint,
        )
        for pack_id, capability, status, quality, order, dependency, runtime_entrypoint in values
    ]


def run_dict() -> dict[str, object]:
    return MilestoneCompletionRuntime().run(sample_completion_evidence()).as_dict()
