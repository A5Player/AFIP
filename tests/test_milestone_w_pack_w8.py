import json
from pathlib import Path
from afip.exit_intelligence import (
    FULL_EXIT_REVIEW, MONITOR, PARTIAL_EXIT_REVIEW, WAIT_DATA,
    ExitIntelligenceRuntime, ExitReviewInput,
)

def _item(**changes):
    base = dict(
        position_id="position-001",
        holding_action="EXIT_REVIEW",
        data_integrity_pass=True,
        risk_pass=True,
        execution_pass=True,
        structure_break_score=35,
        regime_reversal_score=30,
        momentum_failure_score=35,
        time_decay_score=25,
        profit_giveback_ratio=0.20,
        exit_evidence_score=30,
        unrealized_points=300,
        protected_points=150,
    )
    base.update(changes)
    return ExitReviewInput(**base)

def test_low_pressure_is_monitor_only():
    result = ExitIntelligenceRuntime().assess(_item())
    assert result.status == MONITOR

def test_material_pressure_escalates_partial_review():
    result = ExitIntelligenceRuntime().assess(
        _item(momentum_failure_score=70, profit_giveback_ratio=0.55)
    )
    assert result.status == PARTIAL_EXIT_REVIEW

def test_dominant_evidence_escalates_full_review():
    runtime = ExitIntelligenceRuntime()
    assert runtime.assess(_item(structure_break_score=85)).status == FULL_EXIT_REVIEW
    assert runtime.assess(_item(regime_reversal_score=90)).status == FULL_EXIT_REVIEW

def test_fail_closed_on_authority_and_upstream_status():
    runtime = ExitIntelligenceRuntime()
    assert runtime.assess(_item(holding_action="HOLD")).status == WAIT_DATA
    assert runtime.assess(_item(data_integrity_pass=False)).status == WAIT_DATA
    assert runtime.assess(_item(risk_pass=False)).status == FULL_EXIT_REVIEW

def test_contract_and_no_execution_authority():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads((root / "config" / "exit_intelligence_runtime_contract.json").read_text(encoding="utf-8"))
    assert contract["fail_closed"] is True
    result = ExitIntelligenceRuntime().assess(_item())
    assert result.order_close_called is False
    assert result.partial_close_called is False
    assert result.execution_authority is False
