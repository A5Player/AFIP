from afip.dashboard_ui import DashboardUIRuntime
from afip.pattern_clustering import PatternClusteringRuntime


def _payload():
    return {
        "similarity_search_ready": True,
        "research_knowledge_approved": True,
        "knowledge_version": "M1.3.0-RESEARCH",
        "patterns": [
            {"pattern_id": "PAT-A", "market_regime": "TRENDING", "features": {"momentum": 0.80, "volatility": 0.40}, "source_lineage": "KR-001"},
            {"pattern_id": "PAT-B", "market_regime": "TRENDING", "features": {"momentum": 0.79, "volatility": 0.41}, "source_lineage": "KR-002"},
            {"pattern_id": "PAT-C", "market_regime": "RANGING", "features": {"momentum": 0.20, "volatility": 0.90}, "source_lineage": "KR-003"},
        ],
        "minimum_similarity": 0.95,
        "future_leakage_detected": False,
        "data_quality_certified": True,
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
        "broker_request_created": False, "order_transmission_attempted": False,
    }


def test_clustering_ready_and_regime_aware():
    report = PatternClusteringRuntime().evaluate_one(_payload())
    assert report.status == "READY"
    assert report.pattern_clustering_enabled is True
    assert report.cluster_count == 2
    assert sorted(cluster.member_count for cluster in report.clusters) == [1, 2]
    assert all(len({cluster.market_regime}) == 1 for cluster in report.clusters)


def test_clusters_are_deterministic_when_input_order_changes():
    runtime = PatternClusteringRuntime()
    first = runtime.evaluate_one(_payload())
    payload = _payload()
    payload["patterns"] = list(reversed(payload["patterns"]))
    second = runtime.evaluate_one(payload)
    assert first.clusters == second.clusters
    assert first.clustering_id == second.clustering_id


def test_feature_order_is_canonical():
    payload = _payload()
    payload["patterns"][0]["features"] = {"volatility": 0.40, "momentum": 0.80}
    assert PatternClusteringRuntime().evaluate_one(payload).status == "READY"


def test_schema_mismatch_within_regime_blocks_clustering():
    payload = _payload()
    payload["patterns"][1]["features"] = {"momentum": 0.79}
    report = PatternClusteringRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert "feature_schema_mismatch" in report.block_reasons


def test_duplicate_pattern_id_blocks_clustering():
    payload = _payload()
    payload["patterns"][1]["pattern_id"] = "PAT-A"
    report = PatternClusteringRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert "duplicate_pattern_ids" in report.block_reasons


def test_execution_remains_locked():
    payload = _payload()
    payload["live_execution_enabled"] = True
    payload["order_status"] = "ORDER_SENT"
    report = PatternClusteringRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert report.live_execution_enabled is False
    assert report.order_transmission_attempted is False


def test_dashboard_contains_pattern_clustering_panel():
    report = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "profile_name": "Research"})
    assert "pattern_clustering" in {panel.panel_id for panel in report.panels}
