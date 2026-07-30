import json
from pathlib import Path

from afip.advisory_certification import (
    BLOCKED,
    CERTIFIED,
    REVIEW_REQUIRED,
    AdvisoryCertificationRuntime,
)

COMPONENTS = (
    ("W2", "afip/context_matching/engine.py", "config/context_matching_contract.json"),
    ("W3", "afip/strategy_intelligence/engine.py", "config/strategy_intelligence_contract.json"),
    ("W4", "afip/trading_plan_selection/engine.py", "config/trading_plan_selection_contract.json"),
    ("W5", "afip/opportunity_quality/engine.py", "config/opportunity_quality_runtime_contract.json"),
    ("W6", "afip/adaptive_sl/engine.py", "config/adaptive_sl_runtime_contract.json"),
    ("W7", "afip/holding_intelligence/engine.py", "config/holding_intelligence_runtime_contract.json"),
    ("W8", "afip/exit_intelligence/engine.py", "config/exit_intelligence_runtime_contract.json"),
    ("W9", "afip/advisory_orchestration/engine.py", "config/advisory_orchestration_contract.json"),
)

def _build(root: Path, *, break_boundary=False):
    for i, (_, module_rel, contract_rel) in enumerate(COMPONENTS):
        module = root / module_rel
        contract = root / contract_rel
        module.parent.mkdir(parents=True, exist_ok=True)
        contract.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("# module\n", encoding="utf-8")
        body = {
            "authority": "TRACE_AND_VALIDATION_ONLY" if "orchestration" in contract_rel else "ADVISORY_ONLY",
            "forbidden_authorities": ["ORDER_SEND"],
        }
        if break_boundary and i == 0:
            body["execution_authority"] = True
        contract.write_text(json.dumps(body), encoding="utf-8")

def test_complete_foundation_is_certified(tmp_path):
    _build(tmp_path)
    result = AdvisoryCertificationRuntime(COMPONENTS).certify(tmp_path)
    assert result.status == CERTIFIED
    assert result.passed_count == result.required_count
    assert result.authority_boundary_passed is True

def test_missing_component_requires_review(tmp_path):
    _build(tmp_path)
    (tmp_path / COMPONENTS[0][1]).unlink()
    result = AdvisoryCertificationRuntime(COMPONENTS).certify(tmp_path)
    assert result.status == REVIEW_REQUIRED
    assert result.reason == "required_component_incomplete"

def test_authority_violation_blocks_certification(tmp_path):
    _build(tmp_path, break_boundary=True)
    result = AdvisoryCertificationRuntime(COMPONENTS).certify(tmp_path)
    assert result.status == BLOCKED
    assert result.reason == "certification_blocker_detected"

def test_snapshot_identity_is_deterministic(tmp_path):
    _build(tmp_path)
    runtime = AdvisoryCertificationRuntime(COMPONENTS)
    first = runtime.certify(tmp_path)
    second = runtime.certify(tmp_path)
    assert first.snapshot_digest == second.snapshot_digest
    assert first.snapshot_id == second.snapshot_id

def test_contract_and_no_execution_authority(tmp_path):
    _build(tmp_path)
    result = AdvisoryCertificationRuntime(COMPONENTS).certify(tmp_path)
    assert result.execution_authority is False
    assert result.order_send_called is False
    assert result.order_modify_called is False
    assert result.order_close_called is False

    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "config" / "advisory_certification_contract.json").read_text(encoding="utf-8")
    )
    assert contract["authority"] == "READ_ONLY_CERTIFICATION"
    assert contract["fail_closed"] is True
