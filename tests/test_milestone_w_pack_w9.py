import json
from pathlib import Path
from afip.advisory_orchestration import (
    STAGE_ORDER, TRACE_BLOCKED, TRACE_COMPLETE, TRACE_WAIT,
    AdvisoryOrchestrator, AdvisoryStage,
)

def _stages(count=7, authority=True, integrity=True):
    return tuple(
        AdvisoryStage(
            stage=name,
            status="PASS",
            reason=f"{name.lower()}_validated",
            authority_passed=authority,
            data_integrity_passed=integrity,
            payload={"index": i},
        )
        for i, name in enumerate(STAGE_ORDER[:count])
    )

def test_complete_chain_is_validated():
    trace = AdvisoryOrchestrator().build_trace("case-001", _stages())
    assert trace.status == TRACE_COMPLETE
    assert trace.reason == "advisory_chain_validated"

def test_incomplete_chain_waits():
    trace = AdvisoryOrchestrator().build_trace("case-001", _stages(4))
    assert trace.status == TRACE_WAIT
    assert trace.reason == "advisory_chain_incomplete"

def test_invalid_order_is_blocked():
    stages = list(_stages())
    stages[0], stages[1] = stages[1], stages[0]
    trace = AdvisoryOrchestrator().build_trace("case-001", stages)
    assert trace.status == TRACE_BLOCKED
    assert trace.reason == "invalid_stage_order"

def test_authority_and_integrity_fail_closed():
    runtime = AdvisoryOrchestrator()
    assert runtime.build_trace("case-001", _stages(authority=False)).reason == "authority_failure"
    assert runtime.build_trace("case-001", _stages(integrity=False)).reason == "data_integrity_failure"

def test_digest_is_deterministic_and_no_execution_authority():
    runtime = AdvisoryOrchestrator()
    first = runtime.build_trace("case-001", _stages())
    second = runtime.build_trace("case-001", _stages())
    assert first.input_digest == second.input_digest
    assert first.trace_id == second.trace_id
    assert first.execution_authority is False
    assert first.order_send_called is False
    assert first.order_modify_called is False
    assert first.order_close_called is False

    root = Path(__file__).resolve().parents[1]
    contract = json.loads((root / "config" / "advisory_orchestration_contract.json").read_text(encoding="utf-8"))
    assert contract["fail_closed"] is True
