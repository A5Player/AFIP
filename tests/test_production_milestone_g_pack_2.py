from afip.production_event_log import ConfigurationVersionRecord, ProductionEventObservation, ProductionEventRuntime


def _record(**overrides):
    value = {
        "market_regime": "TREND",
        "signal_context": "SELL_CONTINUATION",
        "event_type": "DECISION_REVIEW",
        "event_sequence": 7,
        "config_version": "v2",
        "previous_config_version": "v1",
        "runtime_observability_score": 82,
        "explainability_quality": 86,
        "event_completeness": 88,
        "event_order_quality": 84,
        "config_change_quality": 81,
        "rollback_quality": 83,
        "audit_quality": 85,
    }
    value.update(overrides)
    return value


def test_production_event_log_blocks_records_without_market_regime():
    profile = ProductionEventRuntime().evaluate_one(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.review_required is True
    assert profile.reason == "market_regime_required"


def test_production_event_log_preserves_regime_before_signal_context():
    reports = ProductionEventRuntime().explain_many([
        _record(market_regime="RANGE", signal_context="BUY_PULLBACK", event_sequence=1),
        _record(market_regime="TREND", signal_context="SELL_CONTINUATION", event_sequence=2),
    ])

    assert reports[0].market_regime == "RANGE"
    assert reports[0].signal_context == "BUY_PULLBACK"
    assert reports[1].market_regime == "TREND"
    assert reports[1].signal_context == "SELL_CONTINUATION"


def test_production_event_log_calculates_scores_deterministically():
    profile = ProductionEventRuntime().evaluate_one(_record())

    assert profile.evidence_quality == 0.8405
    assert profile.event_log_score == 0.854
    assert profile.configuration_score == 0.819
    assert profile.audit_score == 0.851
    assert profile.status == "READY"


def test_production_event_log_requires_review_for_low_configuration_quality():
    profile = ProductionEventRuntime().evaluate_one(_record(config_change_quality=42, rollback_quality=82))

    assert profile.status == "REVIEW"
    assert profile.review_required is True
    assert profile.reason == "configuration_version_review_required"


def test_production_event_log_report_contains_config_version_and_reason():
    report = ProductionEventRuntime().explain_one(_record())
    text = report.as_text()

    assert "Market regime: TREND" in text
    assert "Config version: v2" in text
    assert "Previous config version: v1" in text
    assert "Decision reason: production_event_log_ready" in text


def test_production_event_log_observation_and_config_version_helpers():
    observation = ProductionEventObservation.from_mapping(_record(event_completeness=75, event_sequence=-5))
    record = ConfigurationVersionRecord(current_version="v2", previous_version="v1", rollback_available=True)

    assert observation.event_completeness == 0.75
    assert observation.event_sequence == 0
    assert observation.config_changed is True
    assert record.changed is True
    assert record.rollback_status == "ROLLBACK_READY"
