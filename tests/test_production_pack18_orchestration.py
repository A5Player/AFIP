from afip.governance.quality_checkpoint import QualityCheckpoint
from afip.pipeline.production_decision_workflow_v2 import ProductionDecisionWorkflowV2
from afip.report.executive_decision_report import ExecutiveDecisionReport
from afip.runtime.production_orchestrator import ProductionOrchestrator


ALL_CHECKS = (
    "financial_naming_validation",
    "pytest",
    "simulation",
    "mt5_check",
    "github_ci",
)


def test_quality_checkpoint_passes_when_all_required_checks_pass():
    result = QualityCheckpoint().from_completed_names(ALL_CHECKS)
    assert result.status == "PASS"
    assert result.score == 100.0
    assert result.failed_checks == ()


def test_quality_checkpoint_blocks_when_required_check_missing():
    result = QualityCheckpoint().from_completed_names(("pytest", "simulation"))
    assert result.status == "BLOCKED"
    assert "github_ci" in result.failed_checks


def test_production_orchestrator_returns_ready_for_valid_inputs():
    result = ProductionOrchestrator().run(
        decision={"action": "BUY", "confidence": 82},
        readiness={"score": 75},
        risk={"score": 72},
        checkpoint={"status": "PASS"},
    )
    assert result.status == "READY"
    assert result.action == "BUY"


def test_production_orchestrator_waits_when_risk_is_low():
    result = ProductionOrchestrator().run(
        decision={"action": "SELL", "confidence": 80},
        readiness={"score": 80},
        risk={"score": 40},
        checkpoint={"status": "PASS"},
    )
    assert result.status == "WAIT"
    assert result.action == "WAIT"
    assert "risk_score_below_threshold" in result.reason


def test_executive_decision_report_builds_compact_lines():
    report = ExecutiveDecisionReport().build(
        decision={"action": "BUY", "confidence": 88},
        readiness={"score": 81},
        risk={"status": "PASS", "position_size": 0.01},
    )
    assert report.status == "READY"
    assert len(report.lines) == 6
    assert "Decision Action: BUY" in report.lines


def test_production_decision_workflow_v2_ready_path():
    result = ProductionDecisionWorkflowV2().run(
        decision={"action": "BUY", "confidence": 91},
        readiness={"score": 83},
        risk={"score": 77, "position_size": 0.02},
        completed_quality_checks=ALL_CHECKS,
    )
    assert result.status == "READY"
    assert result.action == "BUY"
    assert result.report_lines


def test_production_decision_workflow_v2_blocks_without_quality_checkpoint():
    result = ProductionDecisionWorkflowV2().run(
        decision={"action": "BUY", "confidence": 91},
        readiness={"score": 83},
        risk={"score": 77, "position_size": 0.02},
        completed_quality_checks=("pytest",),
    )
    assert result.status == "WAIT"
    assert result.action == "WAIT"
