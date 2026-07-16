from __future__ import annotations

import json
from pathlib import Path

from afip.research_data_foundation import ResearchRecorder


def ledger_line(**updates):
    value = {
        "profile_id": "P4", "symbol": "GOLD#", "checked_at_utc": "2026-07-15T16:28:00+00:00",
        "status": "ORDER_SENT", "reason": "protected_demo_orders_sent", "decision_action": "SELL",
        "decision_confidence": 100.0, "order_status": "DEMO_ORDER_SENT", "tickets": [11, 12],
        "allocated_lots": [0.01, 0.01], "total_allocated_lot": 0.02,
        "order_check_called": True, "order_send_called": True, "mt5_result_code": 10009,
        "mt5_result_comment": "Request executed", "spread_points": 32.0,
        "caution_spread_points": 25.0, "max_spread_points": 35.0,
        "trading_cost_status": "CAUTION", "trading_cost_allowed": True,
        "point_size": 0.01, "digits": 2,
    }
    value.update(updates)
    return value


def test_ingest_creates_versioned_event_and_trade_case(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps(ledger_line()) + "\n", encoding="utf-8")
    output = tmp_path / "research"
    summary = ResearchRecorder(output).ingest_ledger(ledger)
    assert summary.accepted_events == 1
    assert summary.trade_cases_written == 1
    cases = list((output / "trade_cases").glob("CASE-*.json"))
    assert len(cases) == 1
    case = json.loads(cases[0].read_text(encoding="utf-8"))
    assert case["contract_version"] == "AFIP-RESEARCH-DATA-1.0"
    assert case["tickets"] == [11, 12]
    assert set(case["post_trade_checkpoints"]) == {"M15", "M30", "H1", "H4", "D1"}
    assert case["post_trade_checkpoints"]["M30"]["status"] == "PENDING"


def test_ingest_is_idempotent(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps(ledger_line()) + "\n", encoding="utf-8")
    recorder = ResearchRecorder(tmp_path / "research")
    assert recorder.ingest_ledger(ledger).accepted_events == 1
    second = recorder.ingest_ledger(ledger)
    assert second.accepted_events == 0
    assert second.duplicate_events == 1


def test_wait_event_is_recorded_without_trade_case(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps(ledger_line(status="WAITING", reason="risk_not_approved", tickets=[])) + "\n", encoding="utf-8")
    output = tmp_path / "research"
    summary = ResearchRecorder(output).ingest_ledger(ledger)
    assert summary.accepted_events == 1
    assert summary.trade_cases_written == 0
    event = json.loads((output / "events" / "research_events.jsonl").read_text(encoding="utf-8"))
    assert event["event_type"] == "DECISION_GATE"
    assert event["payload"]["recorded_without_execution_side_effect"] is True


def test_invalid_line_is_quarantined(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("not-json\n", encoding="utf-8")
    output = tmp_path / "research"
    summary = ResearchRecorder(output).ingest_ledger(ledger)
    assert summary.rejected_lines == 1
    assert (output / "rejections" / "rejected_lines.jsonl").exists()
