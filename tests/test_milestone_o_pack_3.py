from afip.learning_evidence_aggregation import LearningEvidenceAggregationRuntime


def _row(i=1, **overrides):
    row = {
        "evidence_record_id": f"OEVN-{i:016X}", "dataset_role": "TRAINING",
        "outcome": "WIN" if i % 2 else "LOSS", "direction": "BUY",
        "observation_timestamp": 1000 + i, "confidence_score": 80.0,
        "realized_r": 1.0 if i % 2 else -0.5,
        "maximum_favourable_excursion_r": 1.5,
        "maximum_adverse_excursion_r": -0.25, "cost_ratio": 0.1,
        "duration_seconds": 3600, "sample_weight": 1.0,
        "evidence_record_accepted": True, "data_quality_certified": True,
        "future_leakage_detected": False, "broker": "XM", "symbol": "GOLD#",
        "base_lot_per_unit": 0.01, "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT", "direct_execution": False,
        "live_execution_enabled": False,
    }
    row.update(overrides)
    return row


def test_ready_report_aggregates_normalized_evidence():
    report = LearningEvidenceAggregationRuntime().evaluate_many([_row(1), _row(2)])
    assert report.status == "READY"
    assert report.sample_count == 2
    assert report.win_count == 1 and report.loss_count == 1
    assert report.average_realized_r == 0.25


def test_report_is_deterministic():
    runtime = LearningEvidenceAggregationRuntime()
    rows = [_row(1), _row(2)]
    assert runtime.evaluate_many(rows) == runtime.evaluate_many(rows)


def test_blocks_dataset_role_contamination():
    report = LearningEvidenceAggregationRuntime().evaluate_many([_row(1), _row(2, dataset_role="HOLDOUT")])
    assert report.status == "BLOCKED"
    assert "dataset_role_contamination" in report.block_reasons


def test_blocks_duplicate_evidence_record_ids():
    report = LearningEvidenceAggregationRuntime().evaluate_many([_row(1), _row(2, evidence_record_id=_row(1)["evidence_record_id"])])
    assert "duplicate_or_invalid_evidence_record_id" in report.block_reasons


def test_blocks_invalid_chronology_and_future_leakage():
    report = LearningEvidenceAggregationRuntime().evaluate_many([_row(1, observation_timestamp=2000), _row(2, observation_timestamp=1000, future_leakage_detected=True)])
    assert "chronological_order_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_blocks_uncertified_pack_2_evidence():
    report = LearningEvidenceAggregationRuntime().evaluate_many([_row(1, evidence_record_accepted=False)])
    assert "pack_2_evidence_not_accepted" in report.block_reasons


def test_blocks_non_finite_metrics():
    report = LearningEvidenceAggregationRuntime().evaluate_many([_row(1, realized_r=float("nan"))])
    assert "non_finite_aggregation_metric" in report.block_reasons


def test_execution_and_adaptive_authority_remain_disabled():
    report = LearningEvidenceAggregationRuntime().evaluate_many([_row(1)])
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
