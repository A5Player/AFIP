from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.regime import MarketRegimeRuntime, RegimeClassifier, RegimeEvidence, RegimeProfileRepository, RegimeThresholdLearner
from afip.runtime.production_milestone_c_market_regime_runtime import run_dict, sample_current_snapshot, sample_regime_evidence


def _evidence(range_percent: float = 1.0, *, regime: str = "expansion", direction: str = "buy") -> RegimeEvidence:
    return RegimeEvidence(
        observed_at=datetime(2026, 1, 7, 8, 0, tzinfo=timezone.utc),
        market_regime=regime,
        volatility_bucket="high",
        direction=direction,
        range_percent=range_percent,
        trend_efficiency=76.0,
        participation_score=82.0,
        transition_pressure=10.0,
        result_amount=14.0,
    )


def test_regime_evidence_normalizes_regime_first_key_before_signal() -> None:
    evidence = _evidence(direction="bullish")
    assert evidence.direction == "BUY"
    assert evidence.regime_first_key == "EXPANSION|HIGH|BUY"


def test_regime_repository_groups_by_market_regime_before_direction() -> None:
    repository = RegimeProfileRepository([_evidence(0.3, regime="quiet", direction="flat"), _evidence(1.2)])
    keys = list(repository.grouped().keys())
    assert keys[0].startswith("EXPANSION|")
    assert keys[1].startswith("QUIET|")


def test_regime_profiles_use_data_derived_metrics() -> None:
    repository = RegimeProfileRepository([_evidence(1.0), _evidence(1.2)])
    profile = repository.profiles()[0]
    assert profile.observations == 2
    assert profile.average_range_percent == 1.1
    assert profile.average_participation_score == 82.0
    assert profile.regime_quality_score > 80.0


def test_threshold_learner_requires_sufficient_evidence() -> None:
    thresholds = RegimeThresholdLearner().learn([_evidence(0.2), _evidence(0.8)])
    assert thresholds is None


def test_threshold_learner_builds_thresholds_from_evidence() -> None:
    thresholds = RegimeThresholdLearner().learn(sample_regime_evidence())
    assert thresholds is not None
    assert thresholds.source_observations == 7
    assert thresholds.quiet_range_percent < thresholds.expansion_range_percent
    assert thresholds.participation_floor > 0


def test_regime_classifier_applies_learned_thresholds_before_signal() -> None:
    thresholds = RegimeThresholdLearner().learn(sample_regime_evidence())
    classification = RegimeClassifier().classify(sample_current_snapshot(), thresholds)
    assert classification.status == "REGIME_CLASSIFICATION_READY"
    assert classification.market_regime == "EXPANSION"
    assert classification.direction_bias == "BUY"
    assert "market_regime_classified_before_signal" in classification.reasons


def test_regime_classifier_blocks_without_learned_thresholds() -> None:
    classification = RegimeClassifier().classify(sample_current_snapshot(), None)
    assert classification.status == "REGIME_DATA_REQUIRED"
    assert classification.confidence == 0.0


def test_market_regime_runtime_builds_ready_state() -> None:
    state = MarketRegimeRuntime().run(sample_regime_evidence(), sample_current_snapshot())
    assert state.status == "MARKET_REGIME_INTELLIGENCE_READY"
    assert state.repository["evidence_count"] == 7
    assert state.classification["market_regime"] == "EXPANSION"


def test_market_regime_runtime_handles_empty_evidence() -> None:
    state = MarketRegimeRuntime().run([], sample_current_snapshot())
    assert state.status == "MARKET_REGIME_DATA_REQUIRED"
    assert state.reason == "insufficient_regime_evidence"


def test_production_milestone_c_market_regime_runtime_is_deterministic() -> None:
    first = run_dict()
    second = run_dict()
    assert first == second
    assert first["status"] == "MARKET_REGIME_INTELLIGENCE_READY"
