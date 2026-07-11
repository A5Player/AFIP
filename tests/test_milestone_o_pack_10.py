from afip.learning_intelligence_complete import LearningIntelligenceCompleteRuntime


def _capability(pack: int, **overrides):
    row = {
        "capability_id": f"OLEARN-{pack:02d}-000000000001",
        "pack": pack,
        "status": "COMPLETE",
        "completed_timestamp": 6000 + pack,
        "data_quality_certified": True,
        "future_safe": True,
        "future_leakage_detected": False,
        "deterministic_runtime": True,
        "dataset_roles_separated": True,
    }
    row.update(overrides)
    return row


def _payload(**overrides):
    payload = {
        "capabilities": [_capability(i) for i in range(1, 10)],
        "pack_9_review": {
            "review_certification_id": "OCERT-0000000000000001",
            "status": "READY",
            "review_certified": True,
            "manual_review_completed": True,
        },
        "data_quality_certified": True,
        "future_safe": True,
        "future_leakage_detected": False,
        "deterministic_runtime": True,
        "dataset_roles_separated": True,
        "policy_version": "AFIP_V1_FEATURE_FREEZE",
        "broker": "XM",
        "symbol": "GOLD#",
        "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT",
        "direct_execution": False,
        "live_execution_enabled": False,
        "automatic_parameter_update_allowed": False,
        "trading_logic_change_allowed": False,
        "production_knowledge_allowed": False,
    }
    payload.update(overrides)
    return payload


def test_ready_report_closes_milestone_o():
    report = LearningIntelligenceCompleteRuntime().evaluate_one(_payload())
    assert report.status == "READY"
    assert report.learning_intelligence_complete is True
    assert report.production_certification_granted is False


def test_report_is_deterministic():
    runtime = LearningIntelligenceCompleteRuntime()
    assert runtime.evaluate_one(_payload()) == runtime.evaluate_one(_payload())


def test_blocks_missing_pack_completion():
    payload = _payload()
    payload["capabilities"] = payload["capabilities"][:-1]
    assert "milestone_o_pack_1_to_9_incomplete" in LearningIntelligenceCompleteRuntime().evaluate_one(payload).block_reasons


def test_blocks_duplicate_capability_lineage():
    payload = _payload()
    payload["capabilities"][-1]["capability_id"] = payload["capabilities"][0]["capability_id"]
    assert "duplicate_or_invalid_learning_capability_lineage" in LearningIntelligenceCompleteRuntime().evaluate_one(payload).block_reasons


def test_blocks_unaccepted_pack_9_review():
    payload = _payload()
    payload["pack_9_review"]["review_certified"] = False
    assert "pack_9_review_certification_not_accepted" in LearningIntelligenceCompleteRuntime().evaluate_one(payload).block_reasons


def test_blocks_chronology_and_future_leakage():
    payload = _payload(future_leakage_detected=True)
    payload["capabilities"][4]["completed_timestamp"] = 1
    report = LearningIntelligenceCompleteRuntime().evaluate_one(payload)
    assert "learning_completion_chronology_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_blocks_data_role_and_deterministic_failures():
    payload = _payload(dataset_roles_separated=False, deterministic_runtime=False, data_quality_certified=False)
    report = LearningIntelligenceCompleteRuntime().evaluate_one(payload)
    assert "dataset_role_separation_not_certified" in report.block_reasons
    assert "deterministic_runtime_not_certified" in report.block_reasons
    assert "data_quality_not_certified" in report.block_reasons


def test_adaptive_production_and_execution_authority_remain_disabled():
    report = LearningIntelligenceCompleteRuntime().evaluate_one(_payload())
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
    assert report.production_certification_granted is False
