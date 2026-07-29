from pathlib import Path

from afip.control_center_runtime import ControlCenterRuntime
from afip.demo_execution_gateway.runtime import DemoGatewayReport


def test_execution_report_has_certified_batch_diagnostics():
    report = DemoGatewayReport(
        profile_id="P1", status="ORDER_SENT", reason="protected_demo_orders_sent",
        account="****0001", server="TEST", symbol="GOLD#",
        execution_batch_id="P1-batch", execution_attempts=2,
        execution_latency_ms=12.5, execution_outcome="COMPLETE",
        unit_results=({"unit_index": 1, "status": "SENT"},),
    ).as_dict()
    assert report["execution_batch_id"] == "P1-batch"
    assert report["execution_outcome"] == "COMPLETE"
    assert report["retry_policy"] == "NO_AUTOMATIC_RETRY_AFTER_AMBIGUOUS_OR_PARTIAL_SEND"
    assert report["reconciliation_required"] is False


def test_dashboard_projects_execution_certification_truth(tmp_path):
    profile = tmp_path / "runtime" / "profiles" / "p1"
    profile.mkdir(parents=True)
    (profile / "demo_execution_state.json").write_text(
        '{"execution_batch_id":"P1-batch","execution_outcome":"PARTIAL_REJECTED",'
        '"execution_attempts":2,"execution_latency_ms":44.2,"partial_execution":true,'
        '"remaining_units":1,"reconciliation_required":true}', encoding="utf-8"
    )
    snapshot = ControlCenterRuntime(tmp_path).snapshot()
    p1 = next(item for item in snapshot["profiles"] if item["profile_id"] == "P1")
    assert p1["execution_outcome"] == "PARTIAL_REJECTED"
    assert p1["reconciliation_required"] is True
    assert p1["remaining_units"] == 1


def test_partial_or_ambiguous_send_persists_duplicate_guard():
    source = Path("afip/demo_execution_gateway/runtime.py").read_text(encoding="utf-8")
    assert 'execution_outcome="AMBIGUOUS_BROKER_RESULT"' in source
    assert 'execution_outcome="PARTIAL_REJECTED" if tickets else "BROKER_REJECTED"' in source
    assert 'state["last_signal_fingerprint"] = fingerprint' in source
    assert 'reconciliation_required=True' in source


def test_execution_is_prechecked_as_complete_batch_before_send():
    source = Path("afip/demo_execution_gateway/runtime.py").read_text(encoding="utf-8")
    assert "prepared_requests: list[dict[str, Any]] = []" in source
    assert source.index("mt5.order_check(request)") < source.index("mt5.order_send(request)")
    assert "complete_trade_plan_not_certified" in source
