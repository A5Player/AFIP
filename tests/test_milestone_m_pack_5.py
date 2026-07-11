from afip.dashboard_ui import DashboardUIRuntime
from afip.pattern_statistics import PatternStatisticsRuntime


def _payload():
    return {
        "pattern_clustering_ready": True,
        "research_knowledge_approved": True,
        "knowledge_version": "M1.5.0-RESEARCH",
        "patterns": [
            {"pattern_id": "PAT-A", "market_regime": "TRENDING", "source_lineage": "KR-001"},
            {"pattern_id": "PAT-B", "market_regime": "TRENDING", "source_lineage": "KR-002"},
        ],
        "clusters": [{
            "cluster_id": "CLU-1", "market_regime": "TRENDING",
            "member_pattern_ids": ["PAT-A", "PAT-B"],
            "source_lineages": ["KR-001", "KR-002"],
        }],
        "outcomes": [
            {"pattern_id": "PAT-A", "accepted": True, "r_multiple": 2.0, "closed_at": "2026-01-01T01:00:00Z", "source_lineage": "OUT-1"},
            {"pattern_id": "PAT-A", "accepted": True, "r_multiple": -1.0, "closed_at": "2026-01-01T02:00:00Z", "source_lineage": "OUT-2"},
            {"pattern_id": "PAT-B", "accepted": False, "r_multiple": 0.5, "closed_at": "2026-01-01T03:00:00Z", "source_lineage": "OUT-3"},
        ],
        "minimum_sample_size": 2,
        "future_leakage_detected": False, "data_quality_certified": True,
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
        "broker_request_created": False, "order_transmission_attempted": False,
    }


def test_statistics_ready_for_patterns_and_clusters():
    report = PatternStatisticsRuntime().evaluate_one(_payload())
    assert report.status == "READY"
    assert report.pattern_statistics_enabled is True
    assert report.statistic_count == 3
    cluster = next(item for item in report.statistics if item.scope_type == "CLUSTER")
    assert cluster.sample_count == 3
    assert cluster.win_count == 2
    assert cluster.loss_count == 1
    assert cluster.expectancy_r == 0.5


def test_statistics_are_deterministic_when_inputs_reordered():
    runtime = PatternStatisticsRuntime()
    first = runtime.evaluate_one(_payload())
    payload = _payload()
    payload["patterns"] = list(reversed(payload["patterns"]))
    payload["clusters"][0]["member_pattern_ids"] = list(reversed(payload["clusters"][0]["member_pattern_ids"]))
    second = runtime.evaluate_one(payload)
    assert first.statistics == second.statistics
    assert first.statistics_id == second.statistics_id


def test_small_sample_is_explicit_not_falsely_certified():
    payload = _payload()
    payload["minimum_sample_size"] = 10
    report = PatternStatisticsRuntime().evaluate_one(payload)
    assert report.status == "READY"
    assert report.sufficient_sample_count == 0
    assert all(item.confidence_tier == "LOW_SAMPLE" for item in report.statistics)


def test_out_of_order_outcomes_block_statistics():
    payload = _payload()
    payload["outcomes"] = list(reversed(payload["outcomes"]))
    report = PatternStatisticsRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert "outcome_chronology_invalid" in report.block_reasons


def test_unknown_pattern_outcome_blocks_statistics():
    payload = _payload()
    payload["outcomes"][0]["pattern_id"] = "PAT-X"
    report = PatternStatisticsRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert "outcome_values_invalid" in report.block_reasons


def test_execution_remains_locked():
    payload = _payload()
    payload["live_execution_enabled"] = True
    payload["order_status"] = "ORDER_SENT"
    report = PatternStatisticsRuntime().evaluate_one(payload)
    assert report.status == "BLOCKED"
    assert report.live_execution_enabled is False
    assert report.order_transmission_attempted is False
    assert report.production_knowledge_approved is False


def test_dashboard_contains_pattern_statistics_panel():
    report = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "profile_name": "Research"})
    assert "pattern_statistics" in {panel.panel_id for panel in report.panels}
