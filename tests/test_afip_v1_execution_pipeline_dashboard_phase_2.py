from pathlib import Path
import json

from afip.dashboard_data_contract import build_dashboard_contract
from afip.execution_pipeline_dashboard import (
    PIPELINE_FILENAME,
    STAGES,
    build_profile_pipeline,
    write_execution_pipeline_dashboard,
)


def test_pipeline_has_certified_order_and_first_block():
    pipeline = build_profile_pipeline({
        "profile_id": "P1",
        "data_status": "FRESH",
        "execution_trace_id": "trace-1",
        "decision_pipeline": {
            "market_feed": "READY",
            "market_regime": "PASS",
            "pattern_recognition": "PASS",
            "multi_timeframe": "PASS",
            "confidence": {"status": "PASS", "value": 99.0},
            "capital_authority": "APPROVED",
            "lot_authority": "APPROVED",
            "risk_authority": "BLOCKED",
        },
        "gateway_reason": "risk_not_approved",
    })
    assert [row["stage_id"] for row in pipeline["stages"]] == [row[0] for row in STAGES]
    assert pipeline["current_stage"] == "risk_authority"
    assert pipeline["trace_id"] == "trace-1"
    assert pipeline["reason"] == "risk_not_approved"


def test_contract_attaches_pipeline_without_calculating_authority(tmp_path: Path):
    (tmp_path / "config").mkdir()
    (tmp_path / "runtime/profiles/p1").mkdir(parents=True)
    (tmp_path / "config/four_profile_demo.json").write_text(json.dumps({
        "profiles": [{"profile_id": "P1", "profile_name": "High Safety", "runtime_directory": "runtime/profiles/p1"}]
    }), encoding="utf-8")
    (tmp_path / "runtime/profiles/p1/demo_execution_state.json").write_text(json.dumps({
        "execution_trace_id": "real-trace",
        "decision_pipeline": {"market_feed": "PASS", "capital_authority": "BLOCKED"},
        "gateway_reason": "capital_insufficient",
    }), encoding="utf-8")
    contract = build_dashboard_contract(tmp_path)
    assert contract["policy"]["dashboard_calculation_authority"] is False
    assert contract["profiles"][0]["execution_pipeline"]["trace_id"] == "real-trace"
    assert contract["profiles"][0]["execution_pipeline"]["current_stage"] == "capital_authority"


def test_pipeline_dashboard_is_generated_and_read_only(tmp_path: Path):
    contract = {
        "generated_at_utc": "2026-07-25T00:00:00Z",
        "execution_pipelines": [build_profile_pipeline({"profile_id": "P4", "order_status": "ORDER_SENT"})],
    }
    output = write_execution_pipeline_dashboard(contract, tmp_path)
    assert output.name == PIPELINE_FILENAME
    html = output.read_text(encoding="utf-8")
    assert "Live Execution Pipeline" in html
    assert "No authority calculation" in html
    assert "MT5 Order Send" in html
    assert 'http-equiv="refresh" content="5"' in html


def test_dashboard_home_registers_pipeline_page():
    source = Path("afip/dashboard_ui/home.py").read_text(encoding="utf-8")
    assert "afip_execution_pipeline_dashboard.html" in source
    assert '"pipeline"' in source
