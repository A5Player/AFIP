from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from afip.research_data_foundation import ResearchRuntimeCollector


def _ledger(path: Path) -> None:
    payload = {"profile_id":"P1","symbol":"GOLD#","status":"ORDER_SENT","reason":"protected_demo_orders_sent",
        "checked_at_utc":"2026-07-16T10:00:00+00:00","decision_action":"BUY","decision_confidence":99.0,
        "tickets":[12345],"order_check_called":True,"order_send_called":True,"pattern_id":"PAT-1"}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload)+"\n", encoding="utf-8")


def test_runtime_collector_is_idempotent_and_research_only(tmp_path: Path) -> None:
    ledger = tmp_path / "p1" / "demo_execution_ledger.jsonl"
    _ledger(ledger)
    collector = ResearchRuntimeCollector(tmp_path / "research")
    first = collector.ingest_ledgers([ledger])
    second = collector.ingest_ledgers([ledger])
    assert first.accepted_events == 1 and first.trade_cases_written == 1
    assert second.duplicate_events == 1
    assert second.research_only is True and second.affects_trading is False


def test_holding_and_exit_update_mfe_mae_and_profit_retention(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"; _ledger(ledger)
    collector = ResearchRuntimeCollector(tmp_path / "research")
    collector.ingest_ledgers([ledger])
    collector.record_position_observation({"ticket":12345,"observed_at_utc":"2026-07-16T10:05:00+00:00","floating_profit":8.0,"sl":3300,"tp":3350})
    case = collector.record_position_observation({"ticket":12345,"observed_at_utc":"2026-07-16T10:10:00+00:00","floating_profit":-3.0})
    assert case["holding_timeline"][-1]["mfe"] == 8.0
    assert case["holding_timeline"][-1]["mae"] == -3.0
    closed = collector.record_closed_trade({"ticket":12345,"observed_at_utc":"2026-07-16T10:20:00+00:00","realized_profit":5.0,"exit_quality":80})
    assert closed["exit_context"]["profit_retained"] == 5.0
    assert closed["exit_context"]["profit_given_back"] == 3.0
    assert closed["lifecycle_state"] == "CLOSED_POST_TRADE_OBSERVATION_PENDING"


def test_due_checkpoint_is_recorded_without_trading_effect(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"; _ledger(ledger)
    collector = ResearchRuntimeCollector(tmp_path / "research")
    collector.ingest_ledgers([ledger])
    observed = (datetime(2026,7,16,10,0,tzinfo=timezone.utc)+timedelta(minutes=15)).isoformat()
    case = collector.record_checkpoint(12345,"M15",observed_at_utc=observed,
        market_snapshot={"bid":3301.0}, assessment={"would_tp_be_reached":False})
    assert case["post_trade_checkpoints"]["M15"]["status"] == "COMPLETED"
    assert case["post_trade_checkpoints"]["M15"]["assessment"]["affects_trading"] is False
