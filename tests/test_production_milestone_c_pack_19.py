from __future__ import annotations

from afip.production_integration import (
    ProductionIntegrationContract,
    ProductionIntegrationPolicy,
    ProductionIntegrationRuntime,
)
from afip.runtime.production_milestone_c_production_integration_runtime import (
    run_dict,
    sample_decision_state,
    sample_execution_state,
    sample_regime_state,
)


def _contract(**updates: object) -> ProductionIntegrationContract:
    data: dict[str, object] = {
        "regime_status": "MARKET_REGIME_INTELLIGENCE_READY",
        "decision_status": "DECISION_INTELLIGENCE_READY",
        "execution_status": "EXECUTION_READY",
        "action": "buy",
        "regime_first_key": "expansion|high|buy",
        "decision_confidence": 82.0,
        "readiness_score": 72.25,
        "spread_points": 24.0,
        "maximum_spread_points": 35.0,
        "reasons": ("production_integration_confirmed",),
    }
    data.update(updates)
    return ProductionIntegrationContract(**data)  # type: ignore[arg-type]


def test_production_integration_contract_normalizes_financial_flow() -> None:
    contract = _contract(action="long", regime_first_key="expansion|high|buy")
    assert contract.action == "WAIT"
    assert contract.regime_first_key == "EXPANSION|HIGH|BUY"
    assert contract.decision_confidence == 82.0


def test_production_integration_contract_reads_regime_decision_execution_states() -> None:
    contract = ProductionIntegrationContract.from_states(sample_regime_state(), sample_decision_state(), sample_execution_state())
    assert contract.regime_status == "MARKET_REGIME_INTELLIGENCE_READY"
    assert contract.decision_status == "DECISION_INTELLIGENCE_READY"
    assert contract.execution_status == "EXECUTION_READY"
    assert contract.regime_first_key == "EXPANSION|HIGH|BUY"


def test_production_integration_requires_market_regime_before_production() -> None:
    decision = ProductionIntegrationPolicy().decide(_contract(regime_status="MARKET_REGIME_DATA_REQUIRED"))
    assert decision.status == "PRODUCTION_DATA_REQUIRED"
    assert decision.action == "WAIT"
    assert "market_regime_required_before_production" in decision.reasons


def test_production_integration_waits_without_ready_decision() -> None:
    decision = ProductionIntegrationPolicy().decide(_contract(decision_status="DECISION_INTELLIGENCE_WAIT"))
    assert decision.status == "PRODUCTION_DECISION_WAIT"
    assert decision.readiness == "WAIT"


def test_production_integration_blocks_without_execution_readiness() -> None:
    decision = ProductionIntegrationPolicy().decide(_contract(execution_status="EXECUTION_BLOCKED"))
    assert decision.status == "PRODUCTION_EXECUTION_BLOCKED"
    assert decision.action == "WAIT"


def test_production_integration_confirms_ready_contract() -> None:
    decision = ProductionIntegrationPolicy().decide(_contract())
    assert decision.status == "PRODUCTION_READY"
    assert decision.action == "BUY"
    assert decision.reasons == ("production_integration_confirmed",)


def test_production_integration_runtime_builds_audit_report() -> None:
    report = ProductionIntegrationRuntime().run(sample_regime_state(), sample_decision_state(), sample_execution_state())
    data = report.as_dict()
    assert data["status"] == "PRODUCTION_READY"
    assert data["audit"]["market_regime_before_decision"] is True
    assert data["audit"]["decision_before_execution"] is True
    assert data["audit"]["execution_after_readiness_checks"] is True


def test_production_integration_runtime_blocks_missing_regime() -> None:
    regime = {"status": "MARKET_REGIME_DATA_REQUIRED", "reason": "insufficient_regime_evidence"}
    report = ProductionIntegrationRuntime().run(regime, sample_decision_state(), sample_execution_state())
    assert report.status == "PRODUCTION_DATA_REQUIRED"
    assert report.decision["action"] == "WAIT"


def test_production_integration_runtime_blocks_execution_failure() -> None:
    execution = sample_execution_state()
    execution["status"] = "EXECUTION_BLOCKED"
    report = ProductionIntegrationRuntime().run(sample_regime_state(), sample_decision_state(), execution)
    assert report.status == "PRODUCTION_EXECUTION_BLOCKED"
    assert report.reason == "execution_readiness_not_confirmed"


def test_production_integration_report_keeps_patch_runtime_deterministic() -> None:
    first = run_dict()
    second = run_dict()
    assert first == second
    assert first["status"] == "PRODUCTION_READY"


def test_production_milestone_c_production_integration_runtime_is_ready() -> None:
    data = run_dict()
    assert data["contract"]["is_ready"] is True
    assert data["decision"]["readiness"] == "READY"
    assert data["reason"] == "production_integration_confirmed"
