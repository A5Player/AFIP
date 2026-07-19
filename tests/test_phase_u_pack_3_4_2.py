from afip.walk_forward_research.runtime import WalkForwardPolicy, WalkForwardResearchEngine, calculate_metrics

def test_drawdown_is_measured_even_with_high_win_rate():
    rows = [{"profit": 1.0}] * 99 + [{"profit": -80.0}]
    metrics = calculate_metrics(rows, starting_equity=100.0)
    assert metrics["win_rate_percentage"] == 99.0
    assert metrics["maximum_drawdown_percentage"] > 40.0

def test_profit_factor_and_expectancy():
    metrics = calculate_metrics([{"profit": 10}, {"profit": -5}, {"profit": 10}])
    assert metrics["profit_factor"] == 4.0
    assert metrics["expectancy"] == 5.0

def test_walk_forward_has_no_overlapping_future_access():
    rows = [{"profit": 1.0} for _ in range(18)]
    policy = WalkForwardPolicy(training_size=6, validation_size=3, out_of_sample_size=3, step_size=3, minimum_trades=3)
    report = WalkForwardResearchEngine(policy).run(rows)
    assert report["window_count"] == 3
    assert report["windows"][0]["out_of_sample_range"] == [9, 12]

def test_drawdown_gate_can_quarantine_high_win_rate():
    rows = [{"profit": 1.0}] * 8 + [{"profit": -60.0}] + [{"profit": 1.0}] * 3
    policy = WalkForwardPolicy(training_size=4, validation_size=4, out_of_sample_size=4, step_size=4, minimum_trades=4, maximum_drawdown_percentage=20.0)
    report = WalkForwardResearchEngine(policy).run(rows, starting_equity=100.0)
    assert report["status"] == "QUARANTINED"
