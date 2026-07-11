from afip.dashboard_ui import DashboardUIRuntime
from afip.knowledge_intelligence_foundation import KnowledgeIntelligenceFoundationRuntime


def _knowledge_records():
    return [
        {
            "record_id": "KR-001", "observed_at_utc": "2026-07-01T01:00:00Z",
            "market_regime": "TRENDING", "feature_vector": {"momentum": 0.8},
            "outcome": {"accepted": True, "r_multiple": 1.2},
            "source_lineage": "PAPER-OUTCOME-001", "explanation": "Momentum aligned with regime.",
        },
        {
            "record_id": "KR-002", "observed_at_utc": "2026-07-01T02:00:00Z",
            "market_regime": "RANGING", "feature_vector": {"momentum": 0.2},
            "outcome": {"accepted": False, "r_multiple": -0.3},
            "source_lineage": "PAPER-OUTCOME-002", "explanation": "Range rejection invalidated continuation.",
        },
    ]


def _record(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "milestone_l_complete": True, "ready_for_milestone_m": True,
        "knowledge_version": "M1.0.0-RESEARCH", "knowledge_records": _knowledge_records(),
        "future_leakage_detected": False, "data_quality_certified": True,
        "execution_status": "LOCKED_SIMULATION_ONLY", "direct_execution": False,
        "live_execution_enabled": False, "order_status": "NO_ORDER_SENT",
        "broker_request_created": False, "order_transmission_attempted": False,
    }
    record.update(extra)
    return record


def test_foundation_accepts_valid_research_knowledge():
    report = KnowledgeIntelligenceFoundationRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.research_knowledge_approved is True
    assert report.production_knowledge_approved is False
    assert report.order_status == "NO_ORDER_SENT"


def test_foundation_id_is_deterministic():
    runtime = KnowledgeIntelligenceFoundationRuntime()
    assert runtime.evaluate_one(_record()).foundation_id == runtime.evaluate_one(_record()).foundation_id


def test_milestone_l_lineage_is_required():
    report = KnowledgeIntelligenceFoundationRuntime().evaluate_one(_record(milestone_l_complete=False))
    assert "milestone_l_not_complete" in report.block_reasons


def test_chronology_and_unique_ids_are_enforced():
    records = _knowledge_records()
    records[1]["observed_at_utc"] = "2026-06-30T23:00:00Z"
    records[1]["record_id"] = "KR-001"
    report = KnowledgeIntelligenceFoundationRuntime().evaluate_one(_record(knowledge_records=records))
    assert "chronological_integrity_invalid" in report.block_reasons
    assert "duplicate_record_ids" in report.block_reasons


def test_schema_lineage_and_explainability_are_required():
    records = _knowledge_records()
    records[0]["feature_vector"] = {}
    records[0]["source_lineage"] = ""
    records[0]["explanation"] = ""
    report = KnowledgeIntelligenceFoundationRuntime().evaluate_one(_record(knowledge_records=records))
    assert "knowledge_records_incomplete" in report.block_reasons
    assert "feature_schema_invalid" in report.block_reasons
    assert "explainability_metadata_missing" in report.block_reasons
    assert "lineage_invalid" in report.block_reasons


def test_execution_and_permanent_policy_are_locked():
    report = KnowledgeIntelligenceFoundationRuntime().evaluate_one(_record(live_execution_enabled=True, broker="OTHER"))
    assert "live_execution_requested" in report.block_reasons
    assert "xm_only_policy" in report.block_reasons
    assert report.direct_execution is False


def test_dashboard_contains_knowledge_intelligence_foundation_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "knowledge_intelligence_foundation" in {panel.panel_id for panel in dashboard.panels}
