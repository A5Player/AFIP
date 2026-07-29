from pathlib import Path
from types import SimpleNamespace
from afip.runtime_truth import build_profile_truth, attach_runtime_truth_model, build_runtime_truth
from afip.dashboard_ui.split_runtime import _research_truth_summary, _live_position_summary
from afip.dashboard_state_machine import normalize_profile_state
from afip.live_mt5_snapshot_authority import publish_live_mt5_snapshot


def test_backward_compatible_runtime_truth_api():
    truth = build_profile_truth({"runtime_state":"RUNNING","process_alive":True,"monitoring_mode":"PASSIVE","connection_status":"CONNECTED_PASSIVE"})
    assert truth["broker_session_state"] == "NOT_VERIFIED"
    assert attach_runtime_truth_model({"profiles":[{"process_alive":False}]})["profiles"][0]["process_state"] == "STOPPED"


def test_live_tick_and_position_helpers(tmp_path: Path):
    state = normalize_profile_state({"runtime_state":"RUNNING","bid":1.0,"ask":1.1,"data_fresh":True,"demo_gateway_status":"WAITING","demo_gateway_reason":"waiting_for_runtime_evidence","source_metadata":{"mt5_health":{"fresh":True},"profile_status":{"fresh":True},"execution_state":{"exists":True,"fresh":True},"runtime_authority":{"fresh":True}}})
    assert state["market_current"] == "OPEN_TICKING"
    assert state["current_reason"] == "waiting_for_next_runtime_cycle"
    assert _live_position_summary({"positions":[{"ticket":123}]})["tickets"] == "123"
    html, status = _research_truth_summary(tmp_path)
    assert status == "INSUFFICIENT_EVIDENCE" and "DATA_UNAVAILABLE" in html


def test_runtime_truth_auditor_uses_semantics_and_freshness(tmp_path: Path):
    # Missing files remain explicit rather than being fabricated.
    report = build_runtime_truth(tmp_path)
    assert report["missing_authority_count"] > 0
    assert report["order_send_called"] is False
