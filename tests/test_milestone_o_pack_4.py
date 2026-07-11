from afip.learning_performance_evaluation import LearningPerformanceEvaluationRuntime


def _row(i=1, **overrides):
    row = {
        "aggregation_record_id": f"OEAG-{i:016X}",
        "dataset_role": "TRAINING" if i == 1 else "EVALUATION",
        "evaluation_timestamp": 1000 + i,
        "sample_count": 10,
        "weighted_sample_count": 10.0,
        "win_count": 6,
        "loss_count": 3,
        "breakeven_count": 1,
        "average_confidence_score": 80.0,
        "average_realized_r": 0.30 if i == 1 else 0.20,
        "total_realized_r": 3.0 if i == 1 else 2.0,
        "aggregation_accepted": True,
        "data_quality_certified": True,
        "future_leakage_detected": False,
        "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
    }
    row.update(overrides)
    return row


def test_ready_report_evaluates_training_and_evaluation_aggregates():
    report = LearningPerformanceEvaluationRuntime().evaluate_many([_row(1), _row(2)])
    assert report.status == "READY"
    assert report.total_sample_count == 20
    assert report.weighted_win_rate == 0.6
    assert report.generalization_gap_r == 0.1


def test_report_is_deterministic():
    runtime = LearningPerformanceEvaluationRuntime()
    rows = [_row(1), _row(2)]
    assert runtime.evaluate_many(rows) == runtime.evaluate_many(rows)


def test_blocks_missing_evaluation_dataset():
    report = LearningPerformanceEvaluationRuntime().evaluate_many([_row(1), _row(2, dataset_role="TRAINING")])
    assert "evaluation_dataset_required" in report.block_reasons


def test_blocks_duplicate_aggregation_record_ids():
    report = LearningPerformanceEvaluationRuntime().evaluate_many([_row(1), _row(2, aggregation_record_id=_row(1)["aggregation_record_id"])])
    assert "duplicate_or_invalid_aggregation_record_id" in report.block_reasons


def test_blocks_invalid_chronology_and_future_leakage():
    report = LearningPerformanceEvaluationRuntime().evaluate_many([
        _row(1, evaluation_timestamp=2000),
        _row(2, evaluation_timestamp=1000, future_leakage_detected=True),
    ])
    assert "chronological_order_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_blocks_uncertified_pack_3_aggregate():
    report = LearningPerformanceEvaluationRuntime().evaluate_many([_row(1), _row(2, aggregation_accepted=False)])
    assert "pack_3_aggregate_not_accepted" in report.block_reasons


def test_blocks_insufficient_or_non_finite_samples():
    report = LearningPerformanceEvaluationRuntime().evaluate_many([
        _row(1, sample_count=0, weighted_sample_count=float("nan")),
        _row(2, sample_count=0),
    ], minimum_sample_count=2)
    assert "minimum_sample_count_not_met" in report.block_reasons
    assert "non_finite_performance_metric" in report.block_reasons


def test_execution_and_adaptive_authority_remain_disabled():
    report = LearningPerformanceEvaluationRuntime().evaluate_many([_row(1), _row(2)])
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
