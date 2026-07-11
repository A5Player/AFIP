from afip.learning_intelligence_foundation import LearningIntelligenceFoundationRuntime


def _valid():
    return {
        "source_record_id": "OUTCOME-001",
        "source_lineage_id": "NCOMP-ABC123",
        "dataset_role": "TRAINING",
        "outcome": "WIN",
        "decision_timestamp": 100,
        "observation_timestamp": 200,
        "source_certified": True,
        "data_quality_certified": True,
        "portfolio_intelligence_complete": True,
    }


def test_accepts_certified_immutable_learning_record():
    report = LearningIntelligenceFoundationRuntime().evaluate_one(_valid())
    assert report.status == "READY"
    assert report.learning_record_accepted is True
    assert report.learning_record_id.startswith("OLRN-")


def test_report_is_deterministic():
    runtime = LearningIntelligenceFoundationRuntime()
    assert runtime.evaluate_one(_valid()) == runtime.evaluate_one(_valid())


def test_blocks_future_leakage_and_invalid_chronology():
    payload = _valid() | {"future_leakage_detected": True, "observation_timestamp": 50}
    report = LearningIntelligenceFoundationRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert "future_leakage_detected" in report.block_reasons
    assert "chronological_order_invalid" in report.block_reasons


def test_blocks_uncertified_or_incomplete_source():
    payload = _valid() | {"source_certified": False, "portfolio_intelligence_complete": False}
    report = LearningIntelligenceFoundationRuntime().evaluate_one(payload)
    assert "source_not_certified" in report.block_reasons
    assert "portfolio_intelligence_incomplete" in report.block_reasons


def test_training_evaluation_holdout_roles_are_separated():
    runtime = LearningIntelligenceFoundationRuntime()
    ids = {runtime.evaluate_one(_valid() | {"dataset_role": role}).learning_record_id for role in ("TRAINING", "EVALUATION", "HOLDOUT")}
    assert len(ids) == 3
    invalid = runtime.evaluate_one(_valid() | {"dataset_role": "PRODUCTION"})
    assert "dataset_role_invalid" in invalid.block_reasons


def test_blocks_mutable_record_and_automatic_updates():
    payload = _valid() | {"mutable_learning_record": True, "automatic_parameter_update_requested": True}
    report = LearningIntelligenceFoundationRuntime().evaluate_one(payload)
    assert "learning_record_must_be_immutable" in report.block_reasons
    assert "automatic_parameter_update_forbidden" in report.block_reasons


def test_execution_safety_is_permanently_locked():
    report = LearningIntelligenceFoundationRuntime().evaluate_one(_valid() | {
        "direct_execution": True,
        "live_execution_enabled": True,
        "broker_request_created": True,
        "order_transmission_attempted": True,
        "position_modification_attempted": True,
    })
    assert report.status == "BLOCKED"
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.order_status == "NO_ORDER_SENT"


def test_locked_policy_metadata_remains_unchanged():
    report = LearningIntelligenceFoundationRuntime().evaluate_one(_valid())
    assert report.broker == "XM"
    assert report.symbol == "GOLD#"
    assert report.base_lot_per_unit == 0.01
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
