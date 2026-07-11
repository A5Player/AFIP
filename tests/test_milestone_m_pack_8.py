from afip.historical_pattern_database import HistoricalPatternDatabaseRuntime


def _record():
    base = {
        "scope_type": "PATTERN", "market_regime": "TREND", "knowledge_version": "M1.8.0-RESEARCH",
        "validated": True, "explanation_status": "EXPLAINED_VALIDATED",
        "feature_schema": ["momentum", "volatility"], "feature_vector": [0.8, 0.3],
        "statistics_lineage": "PSTAT-1", "validation_lineage": "PVAL-1",
        "explainability_lineage": "PEXP-1", "source_lineages": ["KREC-1"],
    }
    one = dict(base, scope_id="PAT-1", observed_at_utc="2026-01-01T00:00:00Z")
    two = dict(base, scope_id="PAT-2", market_regime="RANGE", validated=False,
               explanation_status="EXPLAINED_REJECTED", observed_at_utc="2026-01-02T00:00:00Z")
    return {
        "pattern_explainability_ready": True, "research_knowledge_approved": True,
        "data_quality_certified": True, "historical_records": [two, one],
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
    }


def test_ready_historical_database_snapshot():
    report = HistoricalPatternDatabaseRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.stored_entry_count == 2
    assert report.validated_entry_count == 1
    assert report.rejected_entry_count == 1
    assert report.market_regime_count == 2


def test_deterministic_identity_and_ordering():
    a = HistoricalPatternDatabaseRuntime().evaluate_one(_record())
    record = _record(); record["historical_records"] = list(reversed(record["historical_records"]))
    b = HistoricalPatternDatabaseRuntime().evaluate_one(record)
    assert a.database_id == b.database_id
    assert a.entries == b.entries


def test_duplicate_records_are_deduplicated():
    record = _record(); record["historical_records"].append(dict(record["historical_records"][0]))
    report = HistoricalPatternDatabaseRuntime().evaluate_one(record)
    assert report.status == "READY"
    assert report.duplicate_record_count == 1
    assert report.stored_entry_count == 2


def test_indexes_are_stable_and_searchable():
    report = HistoricalPatternDatabaseRuntime().evaluate_one(_record())
    assert dict(report.regime_index)["TREND"]
    assert dict(report.scope_index)["PAT-1"]


def test_blocks_bad_lineage_and_future_leakage():
    record = _record(); record["historical_records"][0]["source_lineages"] = []
    record["future_leakage_detected"] = True
    report = HistoricalPatternDatabaseRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert "lineage_integrity_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_permanent_execution_lock():
    record = _record(); record["direct_execution"] = True; record["order_transmission_attempted"] = True
    report = HistoricalPatternDatabaseRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert not report.production_knowledge_approved


def test_serializable_research_only_payload():
    payload = HistoricalPatternDatabaseRuntime().evaluate_one(_record()).as_dict()
    assert payload["milestone"] == "M" and payload["pack"] == "8"
    assert payload["research_only"] is True
    assert payload["historical_pattern_database_enabled"] is True
    assert payload["trading_logic_changed"] is False
