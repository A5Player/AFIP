from afip.market_behaviour_validation_governance import MarketBehaviourValidationGovernanceRuntime


def _row(i=1, **overrides):
    row = {
        "calibration_id": f"PBCF-{i:016X}",
        "governance_timestamp": 7000 + i,
        "status": "READY",
        "calibration_accepted": True,
        "confidence_band": "MODERATE",
        "total_transition_count": 162,
        "calibrated_confidence_score": 78.0,
        "data_quality_certified": True,
        "future_safe": True,
        "future_leakage_detected": False,
        "market_regime_before_behaviour": True,
        "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
        "automatic_parameter_update_allowed": False, "trading_logic_change_allowed": False,
        "production_knowledge_allowed": False,
    }
    row.update(overrides)
    return row


def test_ready_report_applies_market_behaviour_validation_governance():
    report = MarketBehaviourValidationGovernanceRuntime().evaluate_many([_row(i) for i in range(1, 4)])
    assert report.status == "READY"
    assert report.governance_accepted is True
    assert report.manual_review_required is True
    assert report.governance_validation_id.startswith("PBGV-")


def test_report_is_deterministic():
    runtime = MarketBehaviourValidationGovernanceRuntime()
    rows = [_row(i) for i in range(1, 4)]
    assert runtime.evaluate_many(rows) == runtime.evaluate_many(rows)


def test_blocks_duplicate_calibration_lineage():
    rows = [_row(i) for i in range(1, 4)]
    rows[-1]["calibration_id"] = rows[0]["calibration_id"]
    report = MarketBehaviourValidationGovernanceRuntime().evaluate_many(rows)
    assert "duplicate_or_invalid_behaviour_confidence_calibration_id" in report.block_reasons


def test_blocks_invalid_chronology_and_future_leakage():
    rows = [_row(i) for i in range(1, 4)]
    rows[-1]["governance_timestamp"] = 100
    rows[1]["future_leakage_detected"] = True
    report = MarketBehaviourValidationGovernanceRuntime().evaluate_many(rows)
    assert "market_behaviour_governance_chronology_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_blocks_unaccepted_pack_7_calibration_and_regime_order():
    rows = [_row(i) for i in range(1, 4)]
    rows[-1]["calibration_accepted"] = False
    rows[1]["market_regime_before_behaviour"] = False
    report = MarketBehaviourValidationGovernanceRuntime().evaluate_many(rows)
    assert "pack_7_behaviour_calibration_not_accepted" in report.block_reasons
    assert "market_regime_not_evaluated_before_behaviour" in report.block_reasons


def test_blocks_role_conflict_and_invalid_policy_version():
    rows = [_row(i) for i in range(1, 4)]
    report = MarketBehaviourValidationGovernanceRuntime().evaluate_many(
        rows, policy_version="UNFROZEN", review_role="SAME_ROLE", approval_role="SAME_ROLE"
    )
    assert "reviewer_approval_role_separation_invalid" in report.block_reasons
    assert "feature_freeze_policy_version_invalid" in report.block_reasons


def test_blocks_insufficient_coverage_and_confidence():
    report = MarketBehaviourValidationGovernanceRuntime().evaluate_many([
        _row(1, total_transition_count=1, calibrated_confidence_score=20.0)
    ])
    assert "minimum_calibration_count_not_met" in report.block_reasons
    assert "minimum_transition_count_not_met" in report.block_reasons
    assert "minimum_behaviour_governance_confidence_not_met" in report.block_reasons


def test_execution_and_adaptive_authority_remain_disabled():
    report = MarketBehaviourValidationGovernanceRuntime().evaluate_many([_row(i) for i in range(1, 4)])
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
    assert report.production_certification_granted is False
    assert report.broker_request_created is False
    assert report.order_transmission_attempted is False
    assert report.position_modification_attempted is False
