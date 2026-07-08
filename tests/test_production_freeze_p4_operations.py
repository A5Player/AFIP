from pathlib import Path

from afip.production_operations import ProductionOperationsObservation, ProductionOperationsRuntime


def _record(**updates):
    data = {
        "market_regime": "TRENDING",
        "signal_context": "SELL_CONTINUATION",
        "execution_mode": "LOCKED_SIMULATION_ONLY",
        "vps_readiness_score": 90,
        "mt5_readiness_score": 88,
        "startup_readiness_score": 84,
        "backup_readiness_score": 86,
        "restore_readiness_score": 82,
        "rollback_readiness_score": 85,
        "operations_checklist_score": 89,
        "monitoring_readiness_score": 87,
        "unresolved_operations_items": 0,
    }
    data.update(updates)
    return data


def test_production_operations_blocks_records_without_market_regime():
    profile = ProductionOperationsRuntime().evaluate_one(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"
    assert profile.operations_gate == "BLOCKED"


def test_production_operations_blocks_live_execution_mode():
    profile = ProductionOperationsRuntime().evaluate_one(_record(execution_mode="LIVE"))

    assert profile.status == "BLOCKED"
    assert profile.reason == "live_execution_not_allowed_for_operations_review"


def test_production_operations_preserves_regime_before_signal_context():
    profile = ProductionOperationsRuntime().evaluate_one(_record(market_regime="sideway", signal_context="buy_reversal"))

    assert profile.market_regime == "SIDEWAY"
    assert profile.signal_context == "BUY_REVERSAL"
    assert profile.status == "READY"


def test_production_operations_calculates_scores_deterministically():
    profile = ProductionOperationsRuntime().evaluate_one(_record())

    expected_deployment = round(
        0.90 * 0.15
        + 0.88 * 0.15
        + 0.84 * 0.12
        + 0.86 * 0.12
        + 0.82 * 0.12
        + 0.85 * 0.12
        + 0.89 * 0.12
        + 0.87 * 0.10,
        6,
    )
    expected_score = round(expected_deployment * 0.84 + 1.0 * 0.16, 6)

    assert profile.deployment_score == expected_deployment
    assert profile.operations_score == expected_score
    assert profile.reason == "production_operations_ready"


def test_production_operations_requires_review_for_unresolved_items():
    profile = ProductionOperationsRuntime().evaluate_one(_record(unresolved_operations_items=1))

    assert profile.status == "REVIEW"
    assert profile.reason == "unresolved_operations_review_required"
    assert profile.operations_gate == "REVIEW_REQUIRED"


def test_production_operations_report_and_files_exist():
    runtime = ProductionOperationsRuntime()
    report = runtime.explain_one(_record(vps_readiness_score=95))
    observation = ProductionOperationsObservation.from_mapping(_record(vps_readiness_score=95))

    assert observation.vps_readiness_score == 0.95
    assert report.as_dict()["operations_gate"] == "PRODUCTION_OPERATIONS_READY"
    assert "Decision reason: production_operations_ready" in report.as_text()
    assert Path("docs/production/AFIP_DEPLOYMENT_GUIDE.md").exists()
    assert Path("docs/production/AFIP_OPERATIONS_CHECKLIST.md").exists()
    assert Path("docs/production/AFIP_BACKUP_RESTORE.md").exists()
    assert Path("docs/production/AFIP_ROLLBACK_GUIDE.md").exists()
