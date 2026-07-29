import json
from pathlib import Path

from afip.runtime_truth import build_runtime_truth
from afip.control_center_runtime import ControlCenterRuntime


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding='utf-8')


def test_runtime_truth_declares_authority_and_never_changes_execution(tmp_path: Path) -> None:
    write_json(tmp_path/'runtime/control/final_integration/desired_runtime_state.json', {'desired_state':'RUNNING'})
    write_json(tmp_path/'runtime/execution/sequential_router_status.json', {'state':'RUNNING','running':True,'pid':123})
    for pid in ('p1','p2','p3','p4'):
        write_json(tmp_path/f'runtime/profiles/{pid}/demo_execution_state.json', {'runtime_state':'RUNNING','order_status':'ORDER_NOT_SENT'})
        write_json(tmp_path/f'runtime/profiles/{pid}/production_activation/position_care_status.json', {'status':'READY','positions_evaluated':0})
    write_json(tmp_path/'runtime/research/runtime_collection_summary.json', {'status':'READY','trade_cases_written':0})
    write_json(tmp_path/'runtime/dashboard/dashboard_monitor_status.json', {'status':'READY'})
    report = build_runtime_truth(tmp_path)
    assert report['status'] == 'CERTIFIED'
    assert report['execution_authority_changed'] is False
    assert report['mt5_initialized'] is False
    assert report['order_send_called'] is False
    assert (tmp_path/'runtime/certification/runtime_truth.json').exists()


def test_runtime_truth_detects_compatibility_conflict(tmp_path: Path) -> None:
    write_json(tmp_path/'runtime/control/final_integration/desired_runtime_state.json', {'status':'RUNNING'})
    write_json(tmp_path/'runtime/final_integration_status.json', {'status':'STOPPED'})
    report = build_runtime_truth(tmp_path)
    assert report['status'] == 'DEGRADED'
    assert report['conflict_count'] >= 1


def test_control_center_projects_runtime_truth(tmp_path: Path) -> None:
    snapshot = ControlCenterRuntime(tmp_path).snapshot()
    assert 'runtime_truth' in snapshot
    assert snapshot['runtime_truth']['policy'] == 'ONE_WRITER_PER_DOMAIN_COMPATIBILITY_READ_ONLY'
