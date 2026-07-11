from afip.learning_evidence_normalization import LearningEvidenceNormalizationRuntime


def _valid():
    return {
        "learning_record_id": "OLRN-1234567890ABCDEF",
        "source_lineage_id": "NCOMP-ABC123",
        "dataset_role": "TRAINING",
        "outcome": "WIN",
        "direction": "BUY",
        "market_regime": "TRENDING_BULLISH",
        "decision_timestamp": 100,
        "observation_timestamp": 200,
        "duration_seconds": 3600,
        "confidence_score": 87.125,
        "realized_r": 1.75,
        "maximum_favourable_excursion_r": 2.25,
        "maximum_adverse_excursion_r": -0.5,
        "cost_ratio": 0.08,
        "sample_weight": 1.0,
        "learning_record_accepted": True,
        "immutable_learning_record": True,
        "data_quality_certified": True,
    }


def test_normalizes_valid_learning_evidence():
    report = LearningEvidenceNormalizationRuntime().evaluate_one(_valid())
    assert report.status == "READY"
    assert report.evidence_record_accepted is True
    assert report.evidence_record_id.startswith("OEVN-")
    assert report.evidence_schema_valid is True


def test_report_is_deterministic_and_canonical():
    runtime = LearningEvidenceNormalizationRuntime()
    first = runtime.evaluate_one(_valid() | {"confidence_score": "87.1250000"})
    second = runtime.evaluate_one(_valid() | {"confidence_score": 87.125})
    assert first == second


def test_blocks_invalid_pack_1_lineage_and_mutability():
    report = LearningEvidenceNormalizationRuntime().evaluate_one(_valid() | {
        "learning_record_id": "INVALID",
        "learning_record_accepted": False,
        "immutable_learning_record": False,
    })
    assert "learning_record_id_invalid" in report.block_reasons
    assert "pack_1_learning_record_not_accepted" in report.block_reasons
    assert "learning_record_not_immutable" in report.block_reasons


def test_blocks_future_leakage_and_invalid_chronology():
    report = LearningEvidenceNormalizationRuntime().evaluate_one(_valid() | {
        "future_leakage_detected": True,
        "observation_timestamp": 50,
    })
    assert "future_leakage_detected" in report.block_reasons
    assert "chronological_order_invalid" in report.block_reasons


def test_blocks_non_finite_and_out_of_range_metrics():
    report = LearningEvidenceNormalizationRuntime().evaluate_one(_valid() | {
        "confidence_score": float("nan"),
        "cost_ratio": 1.5,
        "sample_weight": 0,
        "maximum_adverse_excursion_r": 0.2,
    })
    assert "non_finite_evidence_metric" in report.block_reasons
    assert "evidence_metric_out_of_range" in report.block_reasons


def test_dataset_roles_remain_separated():
    runtime = LearningEvidenceNormalizationRuntime()
    ids = {
        runtime.evaluate_one(_valid() | {"dataset_role": role}).evidence_record_id
        for role in ("TRAINING", "EVALUATION", "HOLDOUT")
    }
    assert len(ids) == 3
    invalid = runtime.evaluate_one(_valid() | {"dataset_role": "PRODUCTION"})
    assert "dataset_role_invalid" in invalid.block_reasons


def test_blocks_adaptive_and_execution_authority():
    report = LearningEvidenceNormalizationRuntime().evaluate_one(_valid() | {
        "automatic_parameter_update_requested": True,
        "trading_logic_change_requested": True,
        "production_knowledge_requested": True,
        "direct_execution": True,
        "live_execution_enabled": True,
        "broker_request_created": True,
        "order_transmission_attempted": True,
        "position_modification_attempted": True,
    })
    assert report.status == "BLOCKED"
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
    assert report.direct_execution is False
    assert report.order_status == "NO_ORDER_SENT"


def test_locked_policy_metadata_remains_unchanged():
    report = LearningEvidenceNormalizationRuntime().evaluate_one(_valid())
    assert report.broker == "XM"
    assert report.symbol == "GOLD#"
    assert report.base_lot_per_unit == 0.01
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.live_execution_enabled is False
    assert report.broker_request_created is False
    assert report.order_transmission_attempted is False
