from afip.production_acceptance_test import ProductionAcceptanceTestObservation, ProductionAcceptanceTestRuntime


def _record(**updates):
    data = {
        "market_regime": "TRENDING",
        "signal_context": "BUY_CONTINUATION",
        "execution_mode": "LOCKED_SIMULATION_ONLY",
        "scenario_type": "HIGH_VOLATILITY_SPREAD_REVIEW",
        "spread_quality_score": 82,
        "margin_quality_score": 88,
        "data_continuity_score": 90,
        "engine_agreement_score": 84,
        "confidence_quality_score": 86,
        "risk_gate_score": 89,
        "decision_consistency_score": 92,
        "blocked_execution_events": 0,
        "unresolved_scenarios": 0,
    }
    data.update(updates)
    return data


def test_production_acceptance_blocks_records_without_market_regime():
    profile = ProductionAcceptanceTestRuntime().evaluate_one(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"
    assert profile.acceptance_gate == "BLOCKED"


def test_production_acceptance_blocks_live_execution_mode():
    profile = ProductionAcceptanceTestRuntime().evaluate_one(_record(execution_mode="LIVE"))

    assert profile.status == "BLOCKED"
    assert profile.reason == "live_execution_not_allowed_for_acceptance_test"


def test_production_acceptance_preserves_regime_before_signal_context():
    profile = ProductionAcceptanceTestRuntime().evaluate_one(_record(market_regime="sideway", signal_context="sell_reversal"))

    assert profile.market_regime == "SIDEWAY"
    assert profile.signal_context == "SELL_REVERSAL"
    assert profile.status == "READY"


def test_production_acceptance_calculates_scores_deterministically():
    profile = ProductionAcceptanceTestRuntime().evaluate_one(_record())

    expected_scenario_quality = round(
        0.82 * 0.13
        + 0.88 * 0.13
        + 0.90 * 0.16
        + 0.84 * 0.15
        + 0.86 * 0.13
        + 0.89 * 0.15
        + 0.92 * 0.15,
        6,
    )
    expected_score = round(expected_scenario_quality * 0.84 + 1.0 * 0.16, 6)

    assert profile.scenario_quality == expected_scenario_quality
    assert profile.acceptance_score == expected_score
    assert profile.reason == "production_acceptance_ready"


def test_production_acceptance_requires_review_for_unresolved_scenarios():
    profile = ProductionAcceptanceTestRuntime().evaluate_one(_record(unresolved_scenarios=1))

    assert profile.status == "REVIEW"
    assert profile.reason == "unresolved_acceptance_scenario_review_required"
    assert profile.acceptance_gate == "REVIEW_REQUIRED"


def test_production_acceptance_report_and_observation_normalizes_percent_values():
    runtime = ProductionAcceptanceTestRuntime()
    report = runtime.explain_one(_record(spread_quality_score=95, scenario_type="mt5_data_gap"))
    observation = ProductionAcceptanceTestObservation.from_mapping(_record(spread_quality_score=95))

    assert observation.spread_quality_score == 0.95
    assert report.as_dict()["acceptance_gate"] == "PRODUCTION_ACCEPTANCE_READY"
    assert "Decision reason: production_acceptance_ready" in report.as_text()
