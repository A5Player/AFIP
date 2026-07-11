from afip.dashboard_ui import DashboardUIRuntime
from afip.pattern_similarity_search import PatternSimilaritySearchRuntime


def _payload():
    return {
        "pattern_engine_ready": True,
        "research_knowledge_approved": True,
        "knowledge_version": "M1.2.0-RESEARCH",
        "query_pattern": {
            "pattern_id": "PAT-Q",
            "market_regime": "TRENDING",
            "features": {"momentum": 0.8, "volatility": 0.4},
            "source_lineage": "ENGINE-M02",
        },
        "candidate_patterns": [
            {"pattern_id": "PAT-A", "market_regime": "TRENDING", "features": {"momentum": 0.79, "volatility": 0.41}, "source_lineage": "KR-001"},
            {"pattern_id": "PAT-B", "market_regime": "TRENDING", "features": {"momentum": 0.70, "volatility": 0.50}, "source_lineage": "KR-002"},
            {"pattern_id": "PAT-C", "market_regime": "RANGING", "features": {"momentum": 0.8, "volatility": 0.4}, "source_lineage": "KR-003"},
        ],
        "minimum_similarity": 0.75,
        "maximum_results": 5,
        "future_leakage_detected": False,
        "data_quality_certified": True,
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
        "broker_request_created": False, "order_transmission_attempted": False,
    }


def test_similarity_search_ready_and_regime_aware():
    report = PatternSimilaritySearchRuntime().evaluate_one(_payload())
    assert report.status == "READY"
    assert report.pattern_search_enabled is True
    assert report.pattern_clustering_enabled is False
    assert report.result_count == 2
    assert "PAT-C" not in report.result_pattern_ids


def test_ranking_is_deterministic():
    runtime = PatternSimilaritySearchRuntime()
    first = runtime.evaluate_one(_payload())
    second_payload = _payload()
    second_payload["candidate_patterns"] = list(reversed(second_payload["candidate_patterns"]))
    second = runtime.evaluate_one(second_payload)
    assert first.result_pattern_ids == second.result_pattern_ids
    assert first.search_id == second.search_id


def test_feature_order_is_canonical():
    payload = _payload()
    payload["query_pattern"]["features"] = {"volatility": 0.4, "momentum": 0.8}
    assert PatternSimilaritySearchRuntime().evaluate_one(payload).status == "READY"


def test_schema_mismatch_blocks_search():
    payload = _payload()
    payload["candidate_patterns"][0]["features"] = {"momentum": 0.79}
    report = PatternSimilaritySearchRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert "feature_schema_mismatch" in report.block_reasons


def test_future_leakage_blocks_search():
    payload = _payload()
    payload["future_leakage_detected"] = True
    report = PatternSimilaritySearchRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert "future_leakage_detected" in report.block_reasons


def test_execution_remains_locked():
    payload = _payload()
    payload["live_execution_enabled"] = True
    payload["order_status"] = "ORDER_SENT"
    report = PatternSimilaritySearchRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert report.live_execution_enabled is False
    assert report.order_transmission_attempted is False


def test_dashboard_contains_similarity_search_panel():
    report = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "profile_name": "Research"})
    assert "pattern_similarity_search" in {panel.panel_id for panel in report.panels}
