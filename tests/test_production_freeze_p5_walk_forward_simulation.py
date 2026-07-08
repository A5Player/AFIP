from afip.walk_forward_simulation import WalkForwardObservation, WalkForwardRuntime


def _record(**updates):
    data = {
        "market_regime": "TRENDING",
        "signal_context": "SELL_CONTINUATION",
        "execution_mode": "LOCKED_SIMULATION_ONLY",
        "historical_window_bars": 500,
        "warmup_bars": 100,
        "revealed_future_bars": 0,
        "simulated_orders": 40,
        "completed_orders": 36,
        "baseline_win_rate": 62,
        "baseline_expectancy": 0.28,
        "max_drawdown_percent": 8,
        "spread_filter_score": 88,
        "regime_coverage_score": 84,
        "standard_quality_score": 86,
        "unresolved_simulation_items": 0,
    }
    data.update(updates)
    return data


def test_walk_forward_blocks_records_without_market_regime():
    profile = WalkForwardRuntime().evaluate_one(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"
    assert profile.simulation_gate == "BLOCKED"


def test_walk_forward_blocks_live_execution_mode():
    profile = WalkForwardRuntime().evaluate_one(_record(execution_mode="LIVE"))

    assert profile.status == "BLOCKED"
    assert profile.reason == "live_execution_not_allowed_for_walk_forward_simulation"


def test_walk_forward_blocks_lookahead_bias():
    profile = WalkForwardRuntime().evaluate_one(_record(revealed_future_bars=1))

    assert profile.status == "BLOCKED"
    assert profile.reason == "lookahead_bias_detected"


def test_walk_forward_preserves_regime_before_signal_context():
    profile = WalkForwardRuntime().evaluate_one(_record(market_regime="sideway", signal_context="buy_reversal"))

    assert profile.market_regime == "SIDEWAY"
    assert profile.signal_context == "BUY_REVERSAL"
    assert profile.status == "READY"


def test_walk_forward_calculates_scores_deterministically():
    profile = WalkForwardRuntime().evaluate_one(_record())

    completion = round(36 / 40, 6)
    expectancy_score = round((0.28 + 1.0) / 2.0, 6)
    drawdown_control = round(1.0 - (0.08 / 0.30), 6)
    expected = round(
        completion * 0.18
        + 0.62 * 0.16
        + expectancy_score * 0.18
        + drawdown_control * 0.14
        + 0.88 * 0.12
        + 0.84 * 0.12
        + 0.86 * 0.10,
        6,
    )

    assert profile.completion_score == completion
    assert profile.expectancy_score == expectancy_score
    assert profile.drawdown_control_score == drawdown_control
    assert profile.acceptance_score == expected
    assert profile.reason == "walk_forward_standard_ready"


def test_walk_forward_report_and_observation_normalizes_percent_values():
    runtime = WalkForwardRuntime()
    report = runtime.explain_one(_record(max_drawdown_percent=12, baseline_win_rate=66))
    observation = WalkForwardObservation.from_mapping(_record(max_drawdown_percent=12, baseline_win_rate=66))

    assert observation.max_drawdown_percent == 0.12
    assert observation.baseline_win_rate == 0.66
    assert report.as_dict()["simulation_gate"] == "WALK_FORWARD_STANDARD_READY"
    assert report.as_dict()["no_lookahead_standard"] is True
    assert "Decision reason: walk_forward_standard_ready" in report.as_text()
