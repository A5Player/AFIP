from afip.learning_confidence_calibration import LearningConfidenceCalibrationRuntime


def _row(i=1, **overrides):
    row = {
        "drift_detection_id": f"ODRF-{i:016X}",
        "calibration_timestamp": 2000 + i,
        "status": "READY",
        "drift_detected": False,
        "baseline_sample_count": 30,
        "recent_sample_count": 30,
        "raw_confidence_score": 82.0,
        "realized_r_drift": 0.05,
        "generalization_gap_drift": 0.04,
        "positive_window_rate_drift": -0.03,
        "data_quality_certified": True,
        "future_safe": True,
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


def test_ready_report_calibrates_research_confidence():
    report = LearningConfidenceCalibrationRuntime().evaluate_many([_row(i) for i in range(1, 4)])
    assert report.status == "READY"
    assert report.calibration_accepted is True
    assert report.calibrated_confidence_score >= 60.0
    assert report.confidence_band in {"CAUTIOUS", "MODERATE", "HIGH"}


def test_report_is_deterministic():
    runtime = LearningConfidenceCalibrationRuntime()
    rows = [_row(i) for i in range(1, 4)]
    assert runtime.evaluate_many(rows) == runtime.evaluate_many(rows)


def test_blocks_duplicate_drift_detection_ids():
    rows = [_row(i) for i in range(1, 4)]
    rows[-1]["drift_detection_id"] = rows[0]["drift_detection_id"]
    report = LearningConfidenceCalibrationRuntime().evaluate_many(rows)
    assert "duplicate_or_invalid_drift_detection_id" in report.block_reasons


def test_blocks_invalid_chronology_and_future_leakage():
    rows = [_row(i) for i in range(1, 4)]
    rows[-1]["calibration_timestamp"] = 100
    rows[1]["future_leakage_detected"] = True
    report = LearningConfidenceCalibrationRuntime().evaluate_many(rows)
    assert "chronological_order_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_blocks_unaccepted_pack_6_drift_report():
    rows = [_row(i) for i in range(1, 4)]
    rows[-1]["drift_detected"] = True
    report = LearningConfidenceCalibrationRuntime().evaluate_many(rows)
    assert "pack_6_drift_not_accepted" in report.block_reasons


def test_blocks_insufficient_report_and_sample_coverage():
    report = LearningConfidenceCalibrationRuntime().evaluate_many([_row(1, baseline_sample_count=1, recent_sample_count=1)])
    assert "minimum_report_count_not_met" in report.block_reasons
    assert "minimum_sample_count_not_met" in report.block_reasons


def test_blocks_low_calibrated_confidence():
    rows = [_row(i, raw_confidence_score=10.0, realized_r_drift=0.34, generalization_gap_drift=0.29, positive_window_rate_drift=0.34) for i in range(1, 4)]
    report = LearningConfidenceCalibrationRuntime().evaluate_many(rows)
    assert "minimum_calibrated_confidence_not_met" in report.block_reasons
    assert report.confidence_band == "INSUFFICIENT"


def test_execution_and_adaptive_authority_remain_disabled():
    report = LearningConfidenceCalibrationRuntime().evaluate_many([_row(i) for i in range(1, 4)])
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
