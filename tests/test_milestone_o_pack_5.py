from afip.learning_stability_validation import LearningStabilityValidationRuntime


def _row(i=1, **overrides):
    row = {
        "performance_evaluation_id": f"OPEV-{i:016X}",
        "dataset_roles": ("TRAINING", "EVALUATION"),
        "stability_window_timestamp": 1000 + i,
        "total_sample_count": 20,
        "evaluation_average_realized_r": 0.20 + (i * 0.01),
        "generalization_gap_r": 0.10,
        "weighted_win_rate": 0.60,
        "weighted_loss_rate": 0.30,
        "weighted_average_confidence_score": 80.0,
        "performance_accepted": True,
        "data_quality_certified": True,
        "future_leakage_detected": False,
        "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
        "automatic_parameter_update_allowed": False,
        "trading_logic_change_allowed": False,
        "production_knowledge_allowed": False,
    }
    row.update(overrides)
    return row


def test_ready_report_validates_stable_evaluation_windows():
    report = LearningStabilityValidationRuntime().evaluate_many([_row(1), _row(2), _row(3)])
    assert report.status == "READY"
    assert report.evaluation_window_count == 3
    assert report.positive_evaluation_window_rate == 1.0
    assert report.stability_accepted is True


def test_report_is_deterministic():
    runtime = LearningStabilityValidationRuntime()
    rows = [_row(1), _row(2), _row(3)]
    assert runtime.evaluate_many(rows) == runtime.evaluate_many(rows)


def test_blocks_duplicate_performance_evaluation_ids():
    report = LearningStabilityValidationRuntime().evaluate_many([
        _row(1), _row(2, performance_evaluation_id=_row(1)["performance_evaluation_id"]), _row(3)
    ])
    assert "duplicate_or_invalid_performance_evaluation_id" in report.block_reasons


def test_blocks_invalid_chronology_and_future_leakage():
    report = LearningStabilityValidationRuntime().evaluate_many([
        _row(1, stability_window_timestamp=3000),
        _row(2, stability_window_timestamp=2000),
        _row(3, stability_window_timestamp=1000, future_leakage_detected=True),
    ])
    assert "chronological_order_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_blocks_uncertified_pack_4_evaluation():
    report = LearningStabilityValidationRuntime().evaluate_many([_row(1), _row(2), _row(3, performance_accepted=False)])
    assert "pack_4_performance_not_accepted" in report.block_reasons


def test_blocks_insufficient_window_and_sample_coverage():
    report = LearningStabilityValidationRuntime().evaluate_many([_row(1, total_sample_count=1)])
    assert "minimum_window_count_not_met" in report.block_reasons
    assert "minimum_total_sample_count_not_met" in report.block_reasons


def test_blocks_unstable_variability_generalization_and_positive_rate():
    report = LearningStabilityValidationRuntime().evaluate_many([
        _row(1, evaluation_average_realized_r=0.8, generalization_gap_r=0.8),
        _row(2, evaluation_average_realized_r=-0.8, generalization_gap_r=-0.8),
        _row(3, evaluation_average_realized_r=-0.7, generalization_gap_r=0.9),
    ])
    assert "evaluation_variability_limit_exceeded" in report.block_reasons
    assert "generalization_gap_limit_exceeded" in report.block_reasons
    assert "positive_window_rate_not_met" in report.block_reasons


def test_execution_and_adaptive_authority_remain_disabled():
    report = LearningStabilityValidationRuntime().evaluate_many([_row(1), _row(2), _row(3)])
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
