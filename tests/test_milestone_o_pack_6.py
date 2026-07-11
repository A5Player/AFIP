from afip.learning_drift_detection import LearningDriftDetectionRuntime


def _row(i=1, **overrides):
    row = {
        "stability_validation_id": f"OSTB-{i:016X}",
        "drift_window_timestamp": 1000 + i,
        "total_sample_count": 20,
        "mean_evaluation_realized_r": 0.25,
        "mean_generalization_gap_r": 0.10,
        "positive_evaluation_window_rate": 0.75,
        "stability_accepted": True,
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


def test_ready_report_confirms_no_material_learning_drift():
    report = LearningDriftDetectionRuntime().evaluate_many([_row(i) for i in range(1, 7)])
    assert report.status == "READY"
    assert report.drift_detected is False
    assert report.realized_r_drift == 0.0


def test_report_is_deterministic():
    runtime = LearningDriftDetectionRuntime()
    rows = [_row(i) for i in range(1, 7)]
    assert runtime.evaluate_many(rows) == runtime.evaluate_many(rows)


def test_blocks_duplicate_stability_validation_ids():
    rows = [_row(i) for i in range(1, 7)]
    rows[-1]["stability_validation_id"] = rows[0]["stability_validation_id"]
    report = LearningDriftDetectionRuntime().evaluate_many(rows)
    assert "duplicate_or_invalid_stability_validation_id" in report.block_reasons


def test_blocks_invalid_chronology_and_future_leakage():
    rows = [_row(i) for i in range(1, 7)]
    rows[3]["drift_window_timestamp"] = 900
    rows[4]["future_leakage_detected"] = True
    report = LearningDriftDetectionRuntime().evaluate_many(rows)
    assert "chronological_order_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_blocks_uncertified_pack_5_stability():
    rows = [_row(i) for i in range(1, 7)]
    rows[-1]["stability_accepted"] = False
    report = LearningDriftDetectionRuntime().evaluate_many(rows)
    assert "pack_5_stability_not_accepted" in report.block_reasons


def test_blocks_insufficient_baseline_and_recent_coverage():
    report = LearningDriftDetectionRuntime().evaluate_many([_row(1, total_sample_count=1), _row(2, total_sample_count=1)])
    assert "insufficient_drift_window_count" in report.block_reasons
    assert "baseline_coverage_not_met" in report.block_reasons
    assert "recent_coverage_not_met" in report.block_reasons


def test_detects_realized_r_gap_and_positive_rate_drift():
    rows = [_row(i) for i in range(1, 4)] + [
        _row(i, mean_evaluation_realized_r=-0.40, mean_generalization_gap_r=0.70, positive_evaluation_window_rate=0.10)
        for i in range(4, 7)
    ]
    report = LearningDriftDetectionRuntime().evaluate_many(rows)
    assert report.drift_detected is True
    assert "realized_r_drift_limit_exceeded" in report.block_reasons
    assert "generalization_gap_drift_limit_exceeded" in report.block_reasons
    assert "positive_window_rate_drift_limit_exceeded" in report.block_reasons


def test_execution_and_adaptive_authority_remain_disabled():
    report = LearningDriftDetectionRuntime().evaluate_many([_row(i) for i in range(1, 7)])
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
