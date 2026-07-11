from afip.pattern_confidence import PatternConfidenceRuntime


def _record():
    return {
        "historical_pattern_database_ready": True,
        "research_knowledge_approved": True,
        "data_quality_certified": True,
        "confidence_scopes": [
            {"scope_id": "PAT-1", "scope_type": "PATTERN", "market_regime": "TREND",
             "sample_count": 120, "expectancy_r": 0.42, "profit_factor": 1.8,
             "dispersion_r": 0.55, "validation_status": "VALIDATED",
             "source_lineages": ["HPD-1", "PVAL-1"]},
            {"scope_id": "PAT-2", "scope_type": "PATTERN", "market_regime": "RANGE",
             "sample_count": 20, "expectancy_r": -0.1, "profit_factor": 0.8,
             "dispersion_r": 1.8, "validation_status": "REJECTED",
             "source_lineages": ["HPD-2", "PVAL-2"]},
        ],
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
    }


def test_ready_confidence_report():
    report = PatternConfidenceRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.scored_scope_count == 2
    assert report.high_confidence_count >= 1


def test_scores_are_bounded_and_explainable():
    report = PatternConfidenceRuntime().evaluate_one(_record())
    assert all(0 <= e.confidence_score <= 100 for e in report.entries)
    assert all(e.confidence_reasons for e in report.entries)


def test_deterministic_order_and_identity():
    a = PatternConfidenceRuntime().evaluate_one(_record())
    record = _record(); record["confidence_scopes"] = list(reversed(record["confidence_scopes"]))
    b = PatternConfidenceRuntime().evaluate_one(record)
    assert a.evaluation_id == b.evaluation_id
    assert a.entries == b.entries


def test_validation_and_statistics_affect_tier():
    report = PatternConfidenceRuntime().evaluate_one(_record())
    by_id = {e.scope_id: e for e in report.entries}
    assert by_id["PAT-1"].confidence_score > by_id["PAT-2"].confidence_score
    assert by_id["PAT-2"].confidence_tier == "LOW"


def test_blocks_bad_lineage_and_future_leakage():
    record = _record(); record["confidence_scopes"][0]["source_lineages"] = []
    record["future_leakage_detected"] = True
    report = PatternConfidenceRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert "lineage_integrity_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_permanent_execution_lock():
    record = _record(); record["direct_execution"] = True; record["order_transmission_attempted"] = True
    report = PatternConfidenceRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert not report.production_knowledge_approved


def test_serializable_research_only_payload():
    payload = PatternConfidenceRuntime().evaluate_one(_record()).as_dict()
    assert payload["milestone"] == "M" and payload["pack"] == "9"
    assert payload["research_only"] is True
    assert payload["pattern_confidence_enabled"] is True
    assert payload["trading_logic_changed"] is False
