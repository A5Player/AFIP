from afip.dashboard_ui import DashboardUIRuntime
from afip.pattern_knowledge_engine import PatternKnowledgeEngineRuntime


def _records():
    return [
        {
            "record_id": "KR-001", "observed_at_utc": "2026-07-01T01:00:00Z",
            "market_regime": "TRENDING", "feature_vector": {"momentum": 0.8, "volatility": 0.4},
            "outcome": {"accepted": True, "r_multiple": 1.2},
            "source_lineage": "PAPER-OUTCOME-001", "explanation": "Momentum aligned with regime.",
        },
        {
            "record_id": "KR-002", "observed_at_utc": "2026-07-01T02:00:00Z",
            "market_regime": "RANGING", "feature_vector": {"momentum": 0.2, "volatility": 0.3},
            "outcome": {"accepted": False, "r_multiple": -0.3},
            "source_lineage": "PAPER-OUTCOME-002", "explanation": "Range rejection invalidated continuation.",
        },
    ]


def _payload():
    return {
        "knowledge_foundation_ready": True,
        "research_knowledge_approved": True,
        "knowledge_version": "M1.1.0-RESEARCH",
        "knowledge_records": _records(),
        "future_leakage_detected": False,
        "data_quality_certified": True,
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
        "broker_request_created": False, "order_transmission_attempted": False,
    }


def test_pattern_knowledge_engine_ready():
    report = PatternKnowledgeEngineRuntime().evaluate_one(_payload())
    assert report.status == "READY"
    assert report.pattern_count == 2
    assert report.accepted_pattern_count == 1
    assert report.pattern_statistics_enabled is True
    assert report.production_knowledge_approved is False


def test_pattern_identity_is_deterministic_and_feature_order_independent():
    runtime = PatternKnowledgeEngineRuntime()
    first = _payload()
    second = _payload()
    second["knowledge_records"][0]["feature_vector"] = {"volatility": 0.4, "momentum": 0.8}
    assert runtime.evaluate_one(first).engine_id == runtime.evaluate_one(second).engine_id


def test_duplicate_patterns_are_aggregated_without_duplicate_identity():
    payload = _payload()
    payload["knowledge_records"].append({**payload["knowledge_records"][0], "record_id": "KR-003"})
    report = PatternKnowledgeEngineRuntime().evaluate_one(payload)
    assert report.status == "READY"
    assert report.source_record_count == 3
    assert report.pattern_count == 2
    assert report.duplicate_pattern_count == 1


def test_future_leakage_blocks_engine():
    payload = _payload()
    payload["future_leakage_detected"] = True
    report = PatternKnowledgeEngineRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert "future_leakage_detected" in report.block_reasons


def test_foundation_and_data_quality_are_required():
    payload = _payload()
    payload["knowledge_foundation_ready"] = False
    payload["data_quality_certified"] = False
    report = PatternKnowledgeEngineRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert "foundation_not_ready" in report.block_reasons
    assert "data_quality_not_certified" in report.block_reasons


def test_execution_policy_cannot_be_enabled():
    payload = _payload()
    payload["live_execution_enabled"] = True
    payload["order_status"] = "ORDER_SENT"
    report = PatternKnowledgeEngineRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert report.live_execution_enabled is False
    assert report.order_status == "ORDER_SENT"
    assert report.order_transmission_attempted is False


def test_dashboard_contains_pattern_knowledge_engine_panel():
    report = DashboardUIRuntime().evaluate_one({
        "broker": "XM", "symbol": "GOLD#", "profile_name": "Research",
        "knowledge_records": _records(), "data_quality_certified": True,
    })
    keys = {panel.panel_id for panel in report.panels}
    assert "pattern_knowledge_engine" in keys
