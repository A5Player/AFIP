from __future__ import annotations

import json
from pathlib import Path
import pytest

from afip.research_data_foundation import GateRecord, HistoricalReplayRecorder, ResearchDashboardSnapshot, ResearchRecorder, TradeLifecycleRecorder
from afip.dashboard_ui import DashboardUIRuntime


def ledger_payload(**updates):
    value = {"checked_at_utc": "2026-07-16T00:00:00+00:00", "profile_id": "P1", "symbol": "GOLD#", "status": "ORDER_SENT",
             "reason": "protected_demo_orders_sent", "decision_action": "BUY", "decision_confidence": 99.0, "order_status": "DEMO_ORDER_SENT",
             "tickets": [101], "order_check_called": True, "order_send_called": True, "pattern": "BREAKOUT", "pattern_id": "PAT-001",
             "pattern_family": "MOMENTUM", "market_regime": "TRENDING", "session": "LONDON", "broker": "XM", "server": "XMGlobal-MT5 6",
             "latency_ms": 12.0, "slippage_points": 1.0, "point_size": 0.01, "digits": 2, "gates": [{"gate": "risk", "outcome": "PASS"}]}
    value.update(updates)
    return value


def create_case(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps(ledger_payload()) + "\n", encoding="utf-8")
    root = tmp_path / "research"
    ResearchRecorder(root).ingest_ledger(ledger)
    path = next((root / "trade_cases").glob("CASE-*.json"))
    return root, json.loads(path.read_text(encoding="utf-8"))["trade_case_id"]


def test_complete_trade_lifecycle_and_checkpoints(tmp_path: Path):
    root, case_id = create_case(tmp_path)
    recorder = TradeLifecycleRecorder(root / "trade_cases")
    case = recorder.load(case_id)
    assert set(case["post_trade_checkpoints"]) == {"M15", "M30", "H1", "H4", "D1"}
    assert case["market_context"]["pattern_id"] == "PAT-001"
    assert case["execution_result"]["broker"] == "XM"
    recorder.append_gate(case_id, GateRecord("spread", "PASS", 20, 35, "within_limit", "2026-07-16T00:01:00+00:00"))
    recorder.append_holding(case_id, {"observed_at_utc": "2026-07-16T00:05:00+00:00", "floating_profit": 5, "floating_loss": 0,
        "mfe": 6, "mae": 1, "sl_movement": "NONE", "tp_movement": "NONE", "break_even": False, "partial_close": False, "trailing_stop": False})
    recorder.record_exit(case_id, {"observed_at_utc": "2026-07-16T00:10:00+00:00", "exit_reason": "target_protection", "exit_quality": 85,
        "profit_retained": 8, "profit_given_back": 2, "net_profit": 8, "mfe": 10, "mae": 1})
    with pytest.raises(ValueError, match="future_data_leakage_blocked"):
        recorder.observe_checkpoint(case_id, "M15", observed_at_utc="2026-07-16T00:14:00+00:00", market_snapshot={}, assessment={})
    case = recorder.observe_checkpoint(case_id, "M15", observed_at_utc="2026-07-16T00:15:00+00:00", market_snapshot={"price": 2500},
        assessment={"was_exit_optimal": True, "would_tp_be_reached": False, "would_sl_be_hit": False, "better_exit_available": False})
    assert case["post_trade_checkpoints"]["M15"]["status"] == "COMPLETED"


def test_replay_is_candle_by_candle_and_blocks_future_leakage(tmp_path: Path):
    replay = HistoricalReplayRecorder(tmp_path / "research" / "replay")
    job = replay.create_job("GOLD#", "M15", "2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00", 2)
    replay.enqueue(job)
    replay.record_candle(job.replay_id, {"close_time_utc": "2026-01-01T00:15:00+00:00", "close": 1},
        visible_history_end_utc="2026-01-01T00:15:00+00:00", decision={"action": "WAIT"})
    with pytest.raises(ValueError, match="future_data_leakage_blocked"):
        replay.record_candle(job.replay_id, {"close_time_utc": "2026-01-01T00:45:00+00:00", "close": 2}, visible_history_end_utc="2026-01-01T00:30:00+00:00")
    stats = json.loads(replay.statistics_path.read_text(encoding="utf-8"))
    assert stats["processed_candles"] == 1 and stats["optimization_enabled"] is False


def test_dashboard_snapshot_and_permanent_panel_are_research_only(tmp_path: Path):
    root, _ = create_case(tmp_path)
    snapshot = ResearchDashboardSnapshot(root).build({"historical_candle_count": 1000, "similarity_percent": 92})
    assert snapshot["dataset"]["trade_case_count"] == 1
    assert snapshot["similar_pattern_monitor"]["affects_trading"] is False
    report = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER", "research_root": str(root)})
    panel = next(item for item in report.panels if item.panel_id == "research_foundation")
    assert panel.rows[-1] or panel.status == "READY"
    assert report.panels[-1].panel_id == "research_foundation"
    assert report.trading_logic_changed is False
