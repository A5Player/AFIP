from afip.feature_flags import FeatureFlagObservation, FeatureFlagRuntime, FeatureFlagState


def _ready_record(**overrides):
    record = {
        "market_regime": "TREND",
        "signal_context": "BREAKOUT",
        "feature_name": "RUNTIME_OBSERVABILITY",
        "current_state": "OFF",
        "requested_state": "ON",
        "configuration_version": "g3.1",
        "production_event_score": 0.86,
        "observability_score": 0.84,
        "rollout_quality": 0.85,
        "rollback_quality": 0.82,
        "dependency_quality": 0.83,
        "operator_review_quality": 0.81,
        "audit_quality": 0.84,
    }
    record.update(overrides)
    return record


def test_feature_flag_blocks_records_without_market_regime():
    profile = FeatureFlagRuntime().evaluate_one(_ready_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"


def test_feature_flag_preserves_regime_before_signal_context():
    profiles = FeatureFlagRuntime().evaluate_many([
        _ready_record(market_regime="RANGE", signal_context="REVERSAL"),
        _ready_record(market_regime="TREND", signal_context="PULLBACK"),
    ])

    assert [profile.market_regime for profile in profiles] == ["RANGE", "TREND"]
    assert [profile.signal_context for profile in profiles] == ["REVERSAL", "PULLBACK"]


def test_feature_flag_calculates_scores_deterministically():
    profile = FeatureFlagRuntime().evaluate_one(_ready_record())

    assert profile.status == "READY"
    assert profile.reason == "feature_flag_ready"
    assert profile.rollout_score == 0.8465
    assert profile.control_score == 0.8215
    assert profile.audit_score == 0.845
    assert profile.state_change_required is True


def test_feature_flag_requires_review_for_low_dependency_quality():
    profile = FeatureFlagRuntime().evaluate_one(_ready_record(dependency_quality=0.50))

    assert profile.status == "REVIEW"
    assert profile.reason == "feature_dependency_review_required"
    assert profile.review_required is True


def test_feature_flag_report_contains_state_and_reason():
    report = FeatureFlagRuntime().explain_one(_ready_record(feature_name="PRODUCTION_EVENT_LOG"))
    text = report.as_text()

    assert "Feature Flag Framework Report" in text
    assert "Feature name: PRODUCTION_EVENT_LOG" in text
    assert "Current state: OFF" in text
    assert "Requested state: ON" in text
    assert "Decision reason: feature_flag_ready" in text


def test_feature_flag_observation_and_state_helpers():
    observation = FeatureFlagObservation.from_mapping(_ready_record(production_event_score=86, enabled=False, desired_state=True))
    state = FeatureFlagState(
        feature_name=observation.feature_name,
        current_state=observation.current_state,
        requested_state=observation.requested_state,
        configuration_version=observation.configuration_version,
        rollback_available=True,
    )

    assert observation.production_event_score == 0.86
    assert observation.current_state == "OFF"
    assert observation.requested_state == "ON"
    assert state.normalized_feature_name == "RUNTIME_OBSERVABILITY"
    assert state.state_changed is True
    assert state.rollout_status == "ROLLOUT_REVIEW_READY"
