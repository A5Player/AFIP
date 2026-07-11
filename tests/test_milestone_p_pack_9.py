from afip.market_behaviour_review_certification import MarketBehaviourReviewCertificationRuntime


def _row(i=1, **overrides):
    row = {
        "governance_validation_id": f"PBGV-{i:016X}",
        "governance_timestamp": 4000 + i,
        "status": "READY",
        "governance_accepted": True,
        "manual_review_required": True,
        "total_transition_count": 60,
        "mean_calibrated_confidence": 78.0,
        "minimum_calibrated_confidence": 70.0,
        "policy_version": "AFIP_V1_FEATURE_FREEZE",
        "data_quality_certified": True,
        "future_safe": True,
        "future_leakage_detected": False,
        "market_regime_before_behaviour": True,
        "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
        "automatic_parameter_update_allowed": False,
        "trading_logic_change_allowed": False,
        "production_knowledge_allowed": False, "production_certification_granted": False,
    }
    row.update(overrides)
    return row


def _evaluate(rows=None, **overrides):
    kwargs = {
        "reviewer_id": "BEHAVIOUR_REVIEWER_001",
        "review_record_id": "PBREV-00000001",
        "review_timestamp": 5000,
        "review_outcome": "APPROVED_FOR_RESEARCH_CONTINUATION",
        "review_notes": "Manual market behaviour research review completed and documented.",
    }
    kwargs.update(overrides)
    return MarketBehaviourReviewCertificationRuntime().evaluate_many(rows or [_row(i) for i in range(1, 4)], **kwargs)


def test_ready_report_certifies_documented_manual_behaviour_review():
    report = _evaluate()
    assert report.status == "READY"
    assert report.review_certified is True
    assert report.manual_review_completed is True
    assert report.review_certification_id.startswith("PBCERT-")


def test_report_is_deterministic():
    rows = [_row(i) for i in range(1, 4)]
    assert _evaluate(rows) == _evaluate(rows)


def test_blocks_duplicate_governance_lineage():
    rows = [_row(i) for i in range(1, 4)]
    rows[-1]["governance_validation_id"] = rows[0]["governance_validation_id"]
    assert "duplicate_or_invalid_behaviour_governance_validation_id" in _evaluate(rows).block_reasons


def test_blocks_invalid_review_chronology_and_future_leakage():
    rows = [_row(i) for i in range(1, 4)]
    rows[1]["future_leakage_detected"] = True
    report = _evaluate(rows, review_timestamp=100)
    assert "behaviour_review_chronology_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_blocks_unaccepted_pack_8_governance():
    rows = [_row(i) for i in range(1, 4)]
    rows[-1]["governance_accepted"] = False
    assert "pack_8_behaviour_governance_not_accepted" in _evaluate(rows).block_reasons


def test_blocks_invalid_manual_review_documentation():
    report = _evaluate(reviewer_id="AUTO", review_record_id="BAD", review_notes="", review_outcome="REJECTED")
    assert "manual_reviewer_identity_invalid" in report.block_reasons
    assert "manual_behaviour_review_record_invalid" in report.block_reasons
    assert "manual_behaviour_review_outcome_not_approved" in report.block_reasons


def test_blocks_insufficient_coverage_and_confidence():
    report = _evaluate([_row(1, total_transition_count=1, mean_calibrated_confidence=20.0, minimum_calibrated_confidence=10.0)])
    assert "minimum_behaviour_governance_report_count_not_met" in report.block_reasons
    assert "minimum_transition_count_not_met" in report.block_reasons
    assert "minimum_behaviour_review_confidence_not_met" in report.block_reasons


def test_execution_and_adaptive_authority_remain_disabled():
    report = _evaluate()
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
    assert report.production_certification_granted is False
