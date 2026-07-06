from afip.adaptive_ai_foundation import (
    AdaptiveAIFoundationObservation,
    AdaptiveAIFoundationPolicy,
    AdaptiveAIFoundationRepository,
    AdaptiveAIFoundationRuntime,
)
from afip.runtime.production_milestone_f_adaptive_ai_foundation_runtime import run_dict, sample_adaptive_ai_observations


def test_adaptive_ai_observation_normalizes_percent_inputs():
    observation = AdaptiveAIFoundationObservation.from_mapping(
        {
            "market_regime": " trend_expansion ",
            "signal": " continuation ",
            "result_amount": "10",
            "confidence": 75,
            "quality": 80,
            "weight": 2,
            "source": " knowledge ",
        }
    )

    assert observation.market_regime == "TREND_EXPANSION"
    assert observation.signal_context == "CONTINUATION"
    assert observation.confidence_score == 0.75
    assert observation.knowledge_quality == 0.8
    assert observation.weighted_result == 20.0
    assert observation.source_key == "KNOWLEDGE"


def test_adaptive_ai_repository_groups_by_market_regime_before_signal_context():
    repository = AdaptiveAIFoundationRepository(sample_adaptive_ai_observations())
    profiles = repository.build_profiles()

    assert [profile.market_regime for profile in profiles] == ["RANGE_COMPRESSION", "TREND_EXPANSION"]
    trend_profile = profiles[1]
    assert trend_profile.sample_count == 2
    assert trend_profile.total_weight == 5.0
    assert trend_profile.weighted_result == 54.0
    assert trend_profile.win_rate == 1.0
    assert trend_profile.adaptive_bias == "POSITIVE_EXPECTANCY"


def test_adaptive_ai_policy_waits_without_market_knowledge():
    decision = AdaptiveAIFoundationPolicy().decide(())

    assert decision.status == "ADAPTIVE_AI_FOUNDATION_WAIT"
    assert decision.readiness == "WAIT"
    assert decision.reason == "market_knowledge_observations_required"


def test_adaptive_ai_policy_blocks_missing_market_regime():
    report = AdaptiveAIFoundationRuntime().run([{"signal_context": "CONTINUATION", "result_amount": 1.0}]).as_dict()

    assert report["status"] == "ADAPTIVE_AI_FOUNDATION_BLOCKED"
    assert report["ready"] is False
    assert report["decision"]["reason"] == "market_regime_required_before_signal_context"


def test_adaptive_ai_runtime_builds_ready_report():
    report = AdaptiveAIFoundationRuntime().run(sample_adaptive_ai_observations()).as_dict()

    assert report["status"] == "ADAPTIVE_AI_FOUNDATION_READY"
    assert report["ready"] is True
    assert report["decision"]["selected_market_regime"] == "TREND_EXPANSION"
    assert report["architecture"]["market_regime_before_signal"] is True
    assert report["architecture"]["deterministic_runtime"] is True


def test_production_milestone_f_pack_1_runtime_is_deterministic():
    first = run_dict()
    second = run_dict()

    assert first == second
    assert first["status"] == "ADAPTIVE_AI_FOUNDATION_READY"
    assert first["profile_count"] == 2
