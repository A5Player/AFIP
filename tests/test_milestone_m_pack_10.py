from afip.knowledge_intelligence_complete import KnowledgeIntelligenceCompleteRuntime


def _record():
    names = (
        "knowledge_intelligence_foundation", "pattern_knowledge_engine",
        "pattern_similarity_search", "pattern_clustering", "pattern_statistics",
        "pattern_validation", "pattern_explainability",
        "historical_pattern_database", "pattern_confidence",
    )
    return {
        "capabilities": {name: True for name in names},
        "capability_lineages": [f"M-{index}" for index in range(1, 10)],
        "data_quality_certified": True,
        "deterministic_runtime_valid": True,
        "market_regime_before_signal": True,
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
    }


def test_ready_completion_report():
    report = KnowledgeIntelligenceCompleteRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.milestone_m_complete is True
    assert report.ready_for_milestone_n is True


def test_requires_every_capability():
    record = _record(); record["capabilities"]["pattern_confidence"] = False
    report = KnowledgeIntelligenceCompleteRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert "pattern_confidence" in report.missing_capabilities


def test_deterministic_identity():
    a = KnowledgeIntelligenceCompleteRuntime().evaluate_one(_record())
    record = _record(); record["capability_lineages"] = list(reversed(record["capability_lineages"]))
    b = KnowledgeIntelligenceCompleteRuntime().evaluate_one(record)
    assert a.completion_id == b.completion_id


def test_blocks_lineage_and_future_leakage():
    record = _record(); record["capability_lineages"] = ["M-1"]; record["future_leakage_detected"] = True
    report = KnowledgeIntelligenceCompleteRuntime().evaluate_one(record)
    assert "capability_lineage_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_market_regime_and_determinism_are_required():
    record = _record(); record["market_regime_before_signal"] = False; record["deterministic_runtime_valid"] = False
    report = KnowledgeIntelligenceCompleteRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert "market_regime_sequence_invalid" in report.block_reasons


def test_permanent_execution_lock_and_no_production_approval():
    record = _record(); record["direct_execution"] = True; record["order_transmission_attempted"] = True
    report = KnowledgeIntelligenceCompleteRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert report.production_knowledge_approved is False


def test_serializable_completion_payload():
    payload = KnowledgeIntelligenceCompleteRuntime().evaluate_one(_record()).as_dict()
    assert payload["milestone"] == "M" and payload["pack"] == "10"
    assert payload["feature_flags"]["portfolio_intelligence_enabled"] is False
    assert payload["trading_logic_changed"] is False
