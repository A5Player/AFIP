from pathlib import Path

from afip.production_documentation import ProductionDocumentationObservation, ProductionDocumentationRuntime


def _record(**updates):
    data = {
        "market_regime": "TRENDING",
        "signal_context": "SELL_CONTINUATION",
        "execution_mode": "LOCKED_SIMULATION_ONLY",
        "architecture_coverage_score": 90,
        "runtime_flow_coverage_score": 88,
        "installation_coverage_score": 84,
        "configuration_coverage_score": 86,
        "recovery_coverage_score": 82,
        "troubleshooting_coverage_score": 87,
        "thai_manual_score": 89,
        "english_manual_score": 91,
        "unresolved_documentation_items": 0,
    }
    data.update(updates)
    return data


def test_production_documentation_blocks_records_without_market_regime():
    profile = ProductionDocumentationRuntime().evaluate_one(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"
    assert profile.documentation_gate == "BLOCKED"


def test_production_documentation_blocks_live_execution_mode():
    profile = ProductionDocumentationRuntime().evaluate_one(_record(execution_mode="LIVE"))

    assert profile.status == "BLOCKED"
    assert profile.reason == "live_execution_not_allowed_for_documentation_review"


def test_production_documentation_preserves_regime_before_signal_context():
    profile = ProductionDocumentationRuntime().evaluate_one(_record(market_regime="sideway", signal_context="buy_reversal"))

    assert profile.market_regime == "SIDEWAY"
    assert profile.signal_context == "BUY_REVERSAL"
    assert profile.status == "READY"


def test_production_documentation_calculates_scores_deterministically():
    profile = ProductionDocumentationRuntime().evaluate_one(_record())

    expected_coverage = round(
        0.90 * 0.16
        + 0.88 * 0.14
        + 0.84 * 0.12
        + 0.86 * 0.12
        + 0.82 * 0.12
        + 0.87 * 0.12
        + 0.89 * 0.11
        + 0.91 * 0.11,
        6,
    )
    expected_score = round(expected_coverage * 0.82 + 1.0 * 0.18, 6)

    assert profile.coverage_score == expected_coverage
    assert profile.documentation_score == expected_score
    assert profile.reason == "production_documentation_ready"


def test_production_documentation_requires_review_for_unresolved_items():
    profile = ProductionDocumentationRuntime().evaluate_one(_record(unresolved_documentation_items=1))

    assert profile.status == "REVIEW"
    assert profile.reason == "unresolved_documentation_review_required"
    assert profile.documentation_gate == "REVIEW_REQUIRED"


def test_production_documentation_report_and_files_exist():
    runtime = ProductionDocumentationRuntime()
    report = runtime.explain_one(_record(architecture_coverage_score=95))
    observation = ProductionDocumentationObservation.from_mapping(_record(architecture_coverage_score=95))

    assert observation.architecture_coverage_score == 0.95
    assert report.as_dict()["documentation_gate"] == "PRODUCTION_DOCUMENTATION_READY"
    assert "Decision reason: production_documentation_ready" in report.as_text()
    assert Path("docs/production/AFIP_PRODUCTION_MANUAL_EN.md").exists()
    assert Path("docs/production/AFIP_PRODUCTION_MANUAL_TH.md").exists()
    assert Path("docs/production/AFIP_RUNTIME_FLOW.md").exists()
    assert Path("docs/production/AFIP_TROUBLESHOOTING.md").exists()
