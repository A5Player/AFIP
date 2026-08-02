from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from afip.research_data_foundation.runtime_collector import ResearchRuntimeCollector
from afip.production_activation_runtime.runtime import ProductionActivationRuntime
from tools.afip_research_runtime_collector import activation_ledger_paths


def _write_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_activation_position_care_and_close_update_same_trade_case(tmp_path: Path) -> None:
    execution = tmp_path / "demo_execution_ledger.jsonl"
    _write_jsonl(execution, {
        "checked_at_utc": "2026-07-29T00:00:00+00:00", "profile_id": "P1", "symbol": "GOLD#",
        "status": "ORDER_SENT", "reason": "protected_demo_orders_sent", "order_status": "DEMO_ORDER_SENT",
        "tickets": [101], "decision_action": "BUY", "decision_confidence": 88.0,
    })
    activation = tmp_path / "activation_ledger.jsonl"
    activation.write_text("\n".join([
        json.dumps({
            "event": "POSITION_CARE", "ticket": 101, "execution_trace_id": "TRACE-1",
            "position_snapshot": {"ticket": "101", "unrealized_profit": 12.5, "observed_at": "2026-07-29T00:10:00+00:00"},
            "position_care": {"recommended_action": "HOLD_POSITION"},
            "intelligence_context": {"selected_scenario": "BUY"},
        }),
        json.dumps({
            "event": "POSITION_CLOSED", "ticket": 101, "realized_profit": 9.0,
            "exit_price": 3400.0, "observed_at_utc": "2026-07-29T01:00:00+00:00",
        }),
    ]) + "\n", encoding="utf-8")
    root = tmp_path / "research"
    summary = ResearchRuntimeCollector(root).ingest_ledgers([execution], [activation])
    assert summary.trade_cases_written == 1
    assert summary.holding_observations == 1
    assert summary.exits_recorded == 1
    case = json.loads(next((root / "trade_cases").glob("CASE-*.json")).read_text(encoding="utf-8"))
    assert case["holding_timeline"][0]["execution_trace_id"] == "TRACE-1"
    assert case["exit_context"]["realized_profit"] == 9.0
    assert case["lifecycle_state"] == "CLOSED_POST_TRADE_OBSERVATION_PENDING"


def test_activation_bridge_is_idempotent(tmp_path: Path) -> None:
    execution = tmp_path / "demo.jsonl"
    _write_jsonl(execution, {"checked_at_utc": "2026-07-29T00:00:00+00:00", "profile_id": "P1", "symbol": "GOLD#", "status": "ORDER_SENT", "reason": "ok", "tickets": [202]})
    activation = tmp_path / "activation.jsonl"
    _write_jsonl(activation, {"event": "POSITION_CARE", "ticket": 202, "position_snapshot": {"ticket": "202", "unrealized_profit": 1.0, "observed_at": "2026-07-29T00:05:00+00:00"}})
    collector = ResearchRuntimeCollector(tmp_path / "research")
    first = collector.ingest_ledgers([execution], [activation])
    second = collector.ingest_ledgers([execution], [activation])
    assert first.holding_observations == 1
    assert second.holding_observations == 0
    assert second.duplicate_events >= 2


def test_closed_position_reconciliation_is_research_only_and_once(tmp_path: Path) -> None:
    profile = SimpleNamespace(profile_id="P1", symbol="GOLD#")
    policy = SimpleNamespace()
    runtime = ProductionActivationRuntime(profile=profile, policy=policy, runtime_root=tmp_path / "runtime")
    plan = runtime.plan_root / "PLAN-X.json"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(json.dumps({"tickets": [303], "plan": {"plan_id": "PLAN-X"}}), encoding="utf-8")
    deal = SimpleNamespace(position_id=303, profit=5.0, swap=-0.2, commission=-0.1, price=3399.5, time=123)
    mt5 = SimpleNamespace(history_deals_get=lambda **kwargs: [deal])
    first = runtime._reconcile_closed_positions(mt5=mt5, open_tickets=set())
    second = runtime._reconcile_closed_positions(mt5=mt5, open_tickets=set())
    assert len(first) == 1 and second == []
    assert first[0]["research_only"] is True
    assert first[0]["affects_trading"] is False
    assert abs(first[0]["realized_profit"] - 4.7) < 1e-9


def test_activation_position_opened_creates_ticket_bound_research_case(tmp_path: Path) -> None:
    activation = tmp_path / "activation.jsonl"
    _write_jsonl(activation, {
        "event": "POSITION_OPENED", "status": "POSITION_OPENED", "tickets": [701, 702],
        "execution_trace_id": "TRACE-OPEN", "updated_at_utc": "2026-08-02T14:20:00+00:00",
        "requests": [{"symbol": "GOLD#", "price": 2400.2, "sl": 2370.2, "tp": 2405.2, "volume": 0.01}],
        "certification": {"status": "CERTIFIED", "plan_id": "PLAN-OPEN"},
        "plan": {
            "plan_id": "PLAN-OPEN", "plan_checksum": "abc", "symbol": "GOLD#",
            "capital": {"profile_id": "P1"},
            "entry": {"direction": "BUY", "maximum_spread_points": 35.0},
            "exit": {"initial_stop_price": 2370.2, "target_prices": [2405.2]},
            "care": {"trailing_policy": "certified_position_care"},
            "market": {"pattern_name": "AFIP_SIGNAL", "pattern_family": "AFIP", "regime": "UNCLASSIFIED", "session": "AUTO", "situation_confidence": 100.0},
        },
    })
    root = tmp_path / "research"
    first = ResearchRuntimeCollector(root).ingest_ledgers([], [activation])
    second = ResearchRuntimeCollector(root).ingest_ledgers([], [activation])
    assert first.accepted_events == 1 and first.trade_cases_written == 1
    assert second.duplicate_events >= 1
    case = json.loads(next((root / "trade_cases").glob("CASE-*.json")).read_text(encoding="utf-8"))
    assert case["tickets"] == [701, 702]
    assert case["profile_id"] == "P1"
    assert case["decision_action"] == "BUY"
    assert case["market_context"]["pattern_id"] == "AFIP_SIGNAL"
    assert case["market_context"]["trading_cost_status"] == "NOT_RECORDED_AT_POSITION_OPEN"
    assert case["data_lineage"]["source_type"] == "PRODUCTION_ACTIVATION_LEDGER"


def test_activation_ledger_paths_use_each_profile_runtime_directory(tmp_path: Path) -> None:
    profiles = [SimpleNamespace(runtime_directory=tmp_path / "p1"), SimpleNamespace(runtime_directory=tmp_path / "p2")]
    assert activation_ledger_paths(profiles) == [
        tmp_path / "p1" / "production_activation" / "activation_ledger.jsonl",
        tmp_path / "p2" / "production_activation" / "activation_ledger.jsonl",
    ]
