from afip.pattern_explainability import PatternExplainabilityRuntime


def _record():
    return {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "pattern_validation_ready": True, "research_knowledge_approved": True,
        "data_quality_certified": True, "knowledge_version": "M1.7.0-RESEARCH",
        "validations": [
            {"scope_id": "PAT-1", "scope_type": "PATTERN", "market_regime": "TRENDING", "validated": True,
             "sample_count": 40, "expectancy_r": 0.30, "profit_factor": 1.70, "win_rate": 0.60,
             "r_standard_deviation": 1.2, "source_lineages": ["LEDGER-A"], "reasons": []},
            {"scope_id": "PAT-2", "scope_type": "PATTERN", "market_regime": "TRENDING", "validated": False,
             "sample_count": 8, "expectancy_r": -0.10, "profit_factor": 0.80, "win_rate": 0.35,
             "r_standard_deviation": 3.5, "source_lineages": ["LEDGER-B"],
             "reasons": ["insufficient_sample", "expectancy_below_threshold"]},
        ],
    }


def test_ready_and_full_coverage():
    report = PatternExplainabilityRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.explained_scope_count == 2
    assert report.validated_scope_count == 1
    assert report.rejected_scope_count == 1
    assert report.explanation_coverage == 1.0


def test_deterministic_identity_and_ordering():
    a = PatternExplainabilityRuntime().evaluate_one(_record())
    record = _record(); record["validations"] = list(reversed(record["validations"]))
    b = PatternExplainabilityRuntime().evaluate_one(record)
    assert a.explainability_id == b.explainability_id
    assert a.explanations == b.explanations


def test_validated_and_rejected_reasons_are_explicit():
    report = PatternExplainabilityRuntime().evaluate_one(_record())
    good = next(item for item in report.explanations if item.scope_id == "PAT-1")
    bad = next(item for item in report.explanations if item.scope_id == "PAT-2")
    assert good.primary_reason == "validated_by_statistical_and_lineage_gates"
    assert bad.primary_reason == "expectancy_below_threshold"
    assert "insufficient_sample" in bad.supporting_reasons


def test_feature_contributions_are_bounded_and_stable():
    report = PatternExplainabilityRuntime().evaluate_one(_record())
    for explanation in report.explanations:
        assert explanation.feature_contributions
        assert all(-1.0 <= value <= 1.0 for _, value in explanation.feature_contributions)


def test_blocks_bad_lineage_and_future_leakage():
    record = _record(); record["validations"][0]["source_lineages"] = []; record["future_leakage_detected"] = True
    report = PatternExplainabilityRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert "validation_lineage_invalid" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons


def test_permanent_execution_lock():
    record = _record(); record["direct_execution"] = True; record["order_transmission_attempted"] = True
    report = PatternExplainabilityRuntime().evaluate_one(record)
    assert report.status == "BLOCKED"
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.order_status == "NO_ORDER_SENT"
    assert not report.production_knowledge_approved


def test_serializable_research_only_payload():
    payload = PatternExplainabilityRuntime().evaluate_one(_record()).as_dict()
    assert payload["milestone"] == "M" and payload["pack"] == "7"
    assert payload["research_only"] is True
    assert payload["pattern_explainability_enabled"] is True
    assert payload["trading_logic_changed"] is False
