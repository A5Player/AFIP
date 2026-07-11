from afip.market_behaviour_intelligence_complete import MarketBehaviourIntelligenceCompleteRuntime


def _capability(pack: int, **overrides):
    row = {
        "capability_id": f"PBEHAV-{pack:02d}-000000000001",
        "pack": pack,
        "status": "COMPLETE",
        "completed_timestamp": 8000 + pack,
        "data_quality_certified": True,
        "future_safe": True,
        "future_leakage_detected": False,
        "deterministic_runtime": True,
        "market_regime_before_behaviour": True,
    }
    row.update(overrides)
    return row


def _payload(**overrides):
    payload = {
        "capabilities": [_capability(i) for i in range(1, 10)],
        "pack_9_review": {
            "review_certification_id": "PBCERT-0000000000000001",
            "status": "READY",
            "review_certified": True,
            "manual_review_completed": True,
        },
        "data_quality_certified": True,
        "future_safe": True,
        "future_leakage_detected": False,
        "deterministic_runtime": True,
        "market_regime_before_behaviour": True,
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
        "production_certification_granted": False,
    }
    payload.update(overrides)
    return payload


def test_ready_report_closes_milestone_p():
    report = MarketBehaviourIntelligenceCompleteRuntime().evaluate_one(_payload())
    assert report.status == "READY"
    assert report.market_behaviour_intelligence_complete is True
    assert report.ready_for_milestone_q is True
    assert report.production_certification_granted is False


def test_report_is_deterministic():
    runtime = MarketBehaviourIntelligenceCompleteRuntime()
    assert runtime.evaluate_one(_payload()) == runtime.evaluate_one(_payload())


def test_blocks_missing_pack_completion():
    payload = _payload()
    payload["capabilities"] = payload["capabilities"][:-1]
    assert "milestone_p_pack_1_to_9_incomplete" in MarketBehaviourIntelligenceCompleteRuntime().evaluate_one(payload).block_reasons


def test_blocks_duplicate_capability_lineage():
    payload = _payload()
    payload["capabilities"][-1]["capability_id"] = payload["capabilities"][0]["capability_id"]
    assert "duplicate_or_invalid_market_behaviour_capability_lineage" in MarketBehaviourIntelligenceCompleteRuntime().evaluate_one(payload).block_reasons


def test_blocks_unaccepted_pack_9_review():
    payload = _payload()
    payload["pack_9_review"]["review_certified"] = False
    assert "pack_9_market_behaviour_review_certification_not_accepted" in MarketBehaviourIntelligenceCompleteRuntime().evaluate_one(payload).block_reasons


def test_blocks_chronology_and_future_leakage():
    payload = _payload(future_leakage_detected=True)
    payload["capabilities"][4]["completed_timestamp"] = 1
    report = MarketBehaviourIntelligenceCompleteRuntime().evaluate_one(payload)
    assert "market_behaviour_completion_chronology_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_blocks_quality_deterministic_and_regime_order_failures():
    payload = _payload(data_quality_certified=False, deterministic_runtime=False, market_regime_before_behaviour=False)
    report = MarketBehaviourIntelligenceCompleteRuntime().evaluate_one(payload)
    assert "data_quality_not_certified" in report.block_reasons
    assert "deterministic_runtime_not_certified" in report.block_reasons
    assert "market_regime_before_behaviour_not_certified" in report.block_reasons


def test_adaptive_production_and_execution_authority_remain_disabled():
    report = MarketBehaviourIntelligenceCompleteRuntime().evaluate_one(_payload())
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
    assert report.production_certification_granted is False
