from afip.learning_validation_governance import LearningValidationGovernanceRuntime


def _row(i=1, **overrides):
    row = {
        "confidence_calibration_id": f"OCAL-{i:016X}",
        "governance_timestamp": 3000 + i,
        "status": "READY",
        "calibration_accepted": True,
        "confidence_band": "MODERATE",
        "total_sample_count": 60,
        "calibrated_confidence_score": 78.0,
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


def test_ready_report_applies_learning_validation_governance():
    report = LearningValidationGovernanceRuntime().evaluate_many([_row(i) for i in range(1, 4)])
    assert report.status == "READY"
    assert report.governance_accepted is True
    assert report.manual_review_required is True


def test_report_is_deterministic():
    runtime = LearningValidationGovernanceRuntime()
    rows = [_row(i) for i in range(1, 4)]
    assert runtime.evaluate_many(rows) == runtime.evaluate_many(rows)


def test_blocks_duplicate_calibration_lineage():
    rows = [_row(i) for i in range(1, 4)]
    rows[-1]["confidence_calibration_id"] = rows[0]["confidence_calibration_id"]
    report = LearningValidationGovernanceRuntime().evaluate_many(rows)
    assert "duplicate_or_invalid_confidence_calibration_id" in report.block_reasons


def test_blocks_invalid_chronology_and_future_leakage():
    rows = [_row(i) for i in range(1, 4)]
    rows[-1]["governance_timestamp"] = 100
    rows[1]["future_leakage_detected"] = True
    report = LearningValidationGovernanceRuntime().evaluate_many(rows)
    assert "chronological_order_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_blocks_unaccepted_pack_7_calibration():
    rows = [_row(i) for i in range(1, 4)]
    rows[-1]["calibration_accepted"] = False
    report = LearningValidationGovernanceRuntime().evaluate_many(rows)
    assert "pack_7_calibration_not_accepted" in report.block_reasons


def test_blocks_role_conflict_and_invalid_policy_version():
    rows = [_row(i) for i in range(1, 4)]
    report = LearningValidationGovernanceRuntime().evaluate_many(
        rows, policy_version="UNFROZEN", review_role="SAME_ROLE", approval_role="SAME_ROLE"
    )
    assert "reviewer_approval_role_separation_invalid" in report.block_reasons
    assert "feature_freeze_policy_version_invalid" in report.block_reasons


def test_blocks_insufficient_coverage_and_confidence():
    report = LearningValidationGovernanceRuntime().evaluate_many([
        _row(1, total_sample_count=1, calibrated_confidence_score=20.0)
    ])
    assert "minimum_calibration_count_not_met" in report.block_reasons
    assert "minimum_sample_count_not_met" in report.block_reasons
    assert "minimum_governance_confidence_not_met" in report.block_reasons


def test_execution_and_adaptive_authority_remain_disabled():
    report = LearningValidationGovernanceRuntime().evaluate_many([_row(i) for i in range(1, 4)])
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
