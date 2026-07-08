from afip.version1_production_freeze import Version1FreezeObservation, Version1FreezeRuntime


def _record(**updates):
    data = {
        "market_regime": "TRENDING",
        "signal_context": "SELL_CONTINUATION",
        "execution_mode": "LOCKED_SIMULATION_ONLY",
        "release_version": "1.0.0",
        "architecture_audit_status": "READY",
        "acceptance_test_status": "READY",
        "documentation_status": "READY",
        "operations_status": "READY",
        "walk_forward_status": "READY",
        "release_candidate_status": "READY",
        "unresolved_release_items": 0,
        "deterministic_runtime_score": 100,
        "backward_compatibility_score": 98,
        "documentation_coverage_score": 94,
        "operations_readiness_score": 92,
        "walk_forward_standard_score": 91,
        "final_quality_score": 96,
    }
    data.update(updates)
    return data


def test_version1_freeze_blocks_records_without_market_regime():
    profile = Version1FreezeRuntime().evaluate_one(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"
    assert profile.freeze_gate == "BLOCKED"


def test_version1_freeze_blocks_live_execution_mode():
    profile = Version1FreezeRuntime().evaluate_one(_record(execution_mode="LIVE"))

    assert profile.status == "BLOCKED"
    assert profile.reason == "live_execution_not_allowed_for_version1_freeze"


def test_version1_freeze_requires_review_for_unresolved_release_items():
    profile = Version1FreezeRuntime().evaluate_one(_record(unresolved_release_items=1))

    assert profile.status == "REVIEW"
    assert profile.reason == "unresolved_release_items_review_required"


def test_version1_freeze_preserves_regime_before_signal_context():
    profile = Version1FreezeRuntime().evaluate_one(_record(market_regime="sideway", signal_context="buy_reversal"))

    assert profile.market_regime == "SIDEWAY"
    assert profile.signal_context == "BUY_REVERSAL"
    assert profile.status == "READY"


def test_version1_freeze_calculates_scores_deterministically():
    profile = Version1FreezeRuntime().evaluate_one(_record())

    expected = round(
        1.00 * 0.20
        + 0.98 * 0.17
        + 0.94 * 0.14
        + 0.92 * 0.14
        + 0.91 * 0.20
        + 0.96 * 0.15,
        6,
    )

    assert profile.release_score == expected
    assert profile.freeze_gate == "VERSION1_PRODUCTION_FREEZE_READY"
    assert profile.reason == "version1_production_freeze_ready"


def test_version1_freeze_report_and_observation_normalizes_percent_values():
    runtime = Version1FreezeRuntime()
    report = runtime.explain_one(_record(deterministic_runtime_score=99, walk_forward_standard_score=88))
    observation = Version1FreezeObservation.from_mapping(
        _record(deterministic_runtime_score=99, walk_forward_standard_score=88)
    )

    assert observation.deterministic_runtime_score == 0.99
    assert observation.walk_forward_standard_score == 0.88
    assert report.as_dict()["freeze_gate"] == "VERSION1_PRODUCTION_FREEZE_READY"
    assert report.as_dict()["version1_frozen"] is True
    assert report.as_dict()["trading_logic_changed"] is False
    assert "Decision reason: version1_production_freeze_ready" in report.as_text()
