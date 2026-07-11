from afip.pattern_validation import PatternValidationRuntime


def _record():
    return {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "pattern_statistics_ready": True, "research_knowledge_approved": True,
        "data_quality_certified": True, "knowledge_version": "M1.6.0-RESEARCH",
        "minimum_sample_size": 20, "minimum_expectancy_r": 0.05,
        "minimum_profit_factor": 1.05, "maximum_r_standard_deviation": 3.0,
        "statistics": [
            {"scope_id": "PAT-1", "scope_type": "PATTERN", "market_regime": "TRENDING", "sample_count": 40,
             "expectancy_r": 0.30, "profit_factor": 1.70, "win_rate": 0.60, "r_standard_deviation": 1.2,
             "confidence_tier": "HIGH", "source_lineages": ["LEDGER-A"]},
            {"scope_id": "PAT-2", "scope_type": "PATTERN", "market_regime": "TRENDING", "sample_count": 8,
             "expectancy_r": -0.10, "profit_factor": 0.8, "win_rate": 0.35, "r_standard_deviation": 3.5,
             "confidence_tier": "LOW_SAMPLE", "source_lineages": ["LEDGER-B"]},
            {"scope_id": "CLU-1", "scope_type": "CLUSTER", "market_regime": "TRENDING", "sample_count": 48,
             "expectancy_r": 0.18, "profit_factor": 1.35, "win_rate": 0.55, "r_standard_deviation": 1.7,
             "confidence_tier": "HIGH", "source_lineages": ["LEDGER-A", "LEDGER-B"]},
        ],
    }


def test_ready_report_and_counts():
    report = PatternValidationRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.validated_pattern_count == 1
    assert report.validated_cluster_count == 1
    assert report.rejected_scope_count == 1


def test_deterministic_identity_and_ordering():
    first = _record()
    second = _record()
    second["statistics"] = list(reversed(second["statistics"]))
    a = PatternValidationRuntime().evaluate_one(first)
    b = PatternValidationRuntime().evaluate_one(second)
    assert a.validation_id == b.validation_id
    assert a.validations == b.validations


def test_explicit_rejection_reasons():
    report = PatternValidationRuntime().evaluate_one(_record())
    rejected = next(item for item in report.validations if item.scope_id == "PAT-2")
    assert not rejected.validated
    assert "insufficient_sample" in rejected.reasons
    assert "expectancy_below_threshold" in rejected.reasons
    assert "profit_factor_below_threshold" in rejected.reasons
    assert "dispersion_above_threshold" in rejected.reasons


def test_blocks_bad_lineage():
    record = _record()
    record["statistics"][0]["source_lineages"] = []
    report = PatternValidationRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert "statistics_lineage_invalid" in report.block_reasons


def test_blocks_future_leakage_and_bad_quality():
    record = _record()
    record["future_leakage_detected"] = True
    record["data_quality_certified"] = False
    report = PatternValidationRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert "future_leakage_detected" in report.block_reasons
    assert "data_quality_not_certified" in report.block_reasons


def test_permanent_execution_lock():
    record = _record()
    record["direct_execution"] = True
    record["order_transmission_attempted"] = True
    report = PatternValidationRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert not report.production_knowledge_approved


def test_serializable_and_research_only():
    report = PatternValidationRuntime().evaluate_one(_record())
    payload = report.as_dict()
    assert payload["milestone"] == "M" and payload["pack"] == "6"
    assert payload["research_only"] is True
    assert payload["pattern_validation_enabled"] is True
    assert payload["trading_logic_changed"] is False
