from __future__ import annotations
import json
from pathlib import Path

from afip.control_center_runtime import ControlCenterRuntime
from afip.dashboard_ui.control_center import render_control_center


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed(tmp_path: Path) -> None:
    write_json(tmp_path / "runtime/control/final_integration/desired_runtime_state.json", {"state":"RUNNING","reason":"operator_start"})
    write_json(tmp_path / "runtime/execution/sequential_router_status.json", {"status":"RUNNING","pid":123})
    write_json(tmp_path / "runtime/dashboard/dashboard_monitor_status.json", {"status":"READY","updated_at_utc":"2026-07-29T00:00:00Z"})
    write_json(tmp_path / "runtime/research/runtime_collection_summary.json", {"status":"READY","trade_cases_written":3,"holding_observations":2,"exits_recorded":1})
    for pid in ("p1","p2","p3","p4"):
        payload={
            "profile_id":pid.upper(),"runtime_state":"RUNNING","connection_status":"CONNECTED","mt5_connection":"CONNECTED",
            "decision":"BUY","confidence":99.2,"waiting_reason":"NONE","execution_trace_id":f"TRACE-{pid}",
            "execution_batch_id":f"BATCH-{pid}","execution_outcome":"COMPLETE","gateway_status":"READY","order_status":"ORDER_SENT",
            "capital_units":1,"risk_units":1,"available_capital":100.0,"limiting_gate":"CAPITAL",
            "intelligence_snapshot":{"decision":{"selected_scenario":"TREND_CONTINUATION","conflict_resolution_reason":"highest_certified_score"}},
            "unit_results":[{"status":"EXECUTED","retcode":10009,"comment":"Request executed"}],
        }
        write_json(tmp_path/f"runtime/profiles/{pid}/demo_execution_state.json", payload)
        write_json(tmp_path/f"runtime/profiles/{pid}/production_activation/position_care_status.json", {
            "status":"READY","positions_evaluated":1,
            "records":[{"ticket":77,"execution_trace_id":f"TRACE-{pid}","position_care":{"recommended_action":"HOLD","reason_codes":["THESIS_VALID"]},"intelligence_context":{"selected_scenario":"TREND_CONTINUATION","decision_confidence":99.2},"mt5_action":{"status":"NO_CHANGE","reason":"hold"}}]
        })


def test_snapshot_exposes_explainability_and_observatory(tmp_path: Path) -> None:
    seed(tmp_path)
    result=ControlCenterRuntime(tmp_path).snapshot()
    assert result["explainability"]["policy"] == "RUNTIME_ARTIFACTS_ONLY_NO_INVENTED_EXPLANATION"
    assert result["runtime_observatory"]["execution_authority_changed"] is False
    assert result["runtime_observatory"]["mt5_auto_launch_allowed"] is False


def test_decision_timeline_has_end_to_end_stages(tmp_path: Path) -> None:
    seed(tmp_path)
    p1=ControlCenterRuntime(tmp_path).snapshot()["explainability"]["profiles"]["P1"]
    names=[row["stage"] for row in p1["stages"]]
    assert names == ["MARKET_DATA","INTELLIGENCE","DECISION","CONFIDENCE","CAPITAL","RISK","EXECUTION","BROKER"]
    assert p1["trace_id"] == "TRACE-p1"
    assert p1["decision"] == "BUY"


def test_broker_explanation_uses_recorded_retcode(tmp_path: Path) -> None:
    seed(tmp_path)
    rows=ControlCenterRuntime(tmp_path).snapshot()["explainability"]["profiles"]["P1"]["stages"]
    broker=next(row for row in rows if row["stage"] == "BROKER")
    assert broker["value"] == 10009
    assert broker["reason"] == "Request executed"


def test_position_explanation_uses_position_care_record(tmp_path: Path) -> None:
    seed(tmp_path)
    row=ControlCenterRuntime(tmp_path).snapshot()["explainability"]["positions"]["P1"]
    assert row["recommended_action"] == "HOLD"
    assert row["reason_codes"] == ["THESIS_VALID"]
    assert row["execution_trace_id"] == "TRACE-p1"


def test_missing_data_is_explicit_not_invented(tmp_path: Path) -> None:
    result=ControlCenterRuntime(tmp_path).snapshot()
    p1=result["explainability"]["profiles"]["P1"]
    assert p1["trace_id"] == "NOT_RECORDED"
    assert p1["source_policy"] == "RUNTIME_ARTIFACTS_ONLY_NO_INVENTED_EXPLANATION"


def test_dashboard_renders_explainable_sections(tmp_path: Path) -> None:
    seed(tmp_path)
    html=render_control_center(tmp_path)
    assert "Explainable Decision Timeline" in html
    assert "Runtime Observatory" in html
    assert "Position Care" in html
    assert "TRACE-p1" in html
    assert "Request executed" in html


def test_pack_is_passive_and_does_not_import_mt5() -> None:
    source=Path("afip/control_center_runtime.py").read_text(encoding="utf-8")
    dashboard=Path("afip/dashboard_ui/control_center.py").read_text(encoding="utf-8")
    assert "order_send(" not in source
    assert "MetaTrader5" not in source
    assert "order_send(" not in dashboard
    assert "MetaTrader5" not in dashboard
