from afip.engine.execution_readiness_engine import ExecutionReadinessEngine
from afip.report.production_readiness_report import ProductionReadinessReport


def test_execution_readiness_allows_clean_checks():
    result = ExecutionReadinessEngine().evaluate({"checks": [
        {"name": "AdaptiveRiskEngine", "status": "READY", "action": "ALLOW", "confidence": 85},
        {"name": "PositionEngine", "status": "READY", "action": "ALLOW", "confidence": 80},
    ]})
    assert result["status"] == "READY"
    assert result["action"] == "ALLOW"


def test_execution_readiness_blocks_failed_check():
    result = ExecutionReadinessEngine().evaluate({"checks": [
        {"name": "AdaptiveRiskEngine", "status": "BLOCKED", "action": "WAIT", "confidence": 20},
        {"name": "PositionEngine", "status": "READY", "action": "ALLOW", "confidence": 80},
    ]})
    assert result["status"] == "BLOCKED"
    assert "AdaptiveRiskEngine" in result["failed_checks"]


def test_production_readiness_report_passes_clean_payload():
    result = ProductionReadinessReport().build([
        {"name": "ExecutionReadinessEngine", "status": "READY", "action": "ALLOW"},
        {"name": "PortfolioEngine", "status": "READY", "action": "ALLOW"},
    ])
    assert result["status"] == "PASS"
    assert result["score"] == 100.0
