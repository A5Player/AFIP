from pathlib import Path
import json

from afip.dashboard_data_contract import build_dashboard_contract
from afip.order_evidence_dashboard import (
    ORDER_EVIDENCE_FILENAME,
    build_order_evidence,
    write_order_evidence_dashboard,
)


def test_order_evidence_keeps_real_execution_fields():
    evidence = build_order_evidence({
        "profile_id": "P1",
        "execution_trace_id": "trace-real",
        "decision": "SELL",
        "confidence": 99.0,
        "approved_units": 2,
        "sent_units": 2,
        "lot_per_unit": 0.01,
        "sl": 3310.5,
        "tp": 3260.0,
        "order_check_called": True,
        "order_send_called": True,
        "mt5_result_code": 10009,
        "tickets": [111, 222],
        "order_status": "ORDER_SENT",
    })
    assert evidence["trace_id"] == "trace-real"
    assert evidence["decision"] == "SELL"
    assert evidence["approved_units"] == 2
    assert evidence["lot_per_unit"] == 0.01
    assert evidence["tickets"] == ["111", "222"]
    assert evidence["evidence_status"] == "ORDER_SENT"


def test_market_closed_is_not_reported_as_runtime_failure():
    evidence = build_order_evidence({
        "profile_id": "P4",
        "market_open": False,
        "order_status": "ORDER_NOT_SENT",
    })
    assert evidence["market_state"] == "MARKET_CLOSED"
    assert evidence["evidence_status"] == "MARKET_CLOSED"
    assert evidence["reason"] == "market_closed_no_new_execution_expected"


def test_contract_attaches_order_evidence_without_calculation(tmp_path: Path):
    (tmp_path / "config").mkdir()
    (tmp_path / "runtime/profiles/p1").mkdir(parents=True)
    (tmp_path / "config/four_profile_demo.json").write_text(json.dumps({
        "profiles": [{"profile_id": "P1", "runtime_directory": "runtime/profiles/p1"}]
    }), encoding="utf-8")
    (tmp_path / "runtime/profiles/p1/demo_execution_state.json").write_text(json.dumps({
        "execution_trace_id": "trace-1",
        "decision": "BUY",
        "approved_units": 1,
        "order_send_called": False,
    }), encoding="utf-8")
    contract = build_dashboard_contract(tmp_path)
    assert contract["policy"]["dashboard_calculation_authority"] is False
    assert contract["order_evidence"][0]["trace_id"] == "trace-1"
    assert contract["order_evidence"][0]["approved_units"] == 1


def test_order_evidence_dashboard_generated_and_registered(tmp_path: Path):
    contract = {
        "generated_at_utc": "2026-07-25T00:00:00Z",
        "order_evidence": [build_order_evidence({"profile_id": "P2", "market_open": False})],
    }
    output = write_order_evidence_dashboard(contract, tmp_path)
    assert output.name == ORDER_EVIDENCE_FILENAME
    html = output.read_text(encoding="utf-8")
    assert "Order Evidence Dashboard" in html
    assert "Market-closed aware" in html
    assert "No MT5 initialization" in html
    assert 'http-equiv="refresh" content="5"' in html
    home = Path("afip/dashboard_ui/home.py").read_text(encoding="utf-8")
    assert "afip_order_evidence_dashboard.html" in home
    assert '"orders"' in home
