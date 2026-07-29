from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from afip.dashboard_data_contract import build_dashboard_contract
from afip.dashboard_state_machine import normalize_profile_state
from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime
from afip.live_mt5_snapshot_authority import publish_live_mt5_snapshot


class MT5Stub:
    def symbol_info_tick(self, symbol: str):
        return SimpleNamespace(bid=4042.10, ask=4042.40)

    def symbol_info(self, symbol: str):
        return SimpleNamespace(point=0.01, digits=2)

    def terminal_info(self):
        return SimpleNamespace(connected=True)

    def positions_get(self, **kwargs):
        return (
            SimpleNamespace(
                ticket=1001, symbol="GOLD#", type=1, volume=0.01,
                price_open=4050.0, price_current=4042.1, sl=4071.3,
                tp=4007.4, profit=7.9, time=1, magic=0, comment="AFIP",
            ),
        )

    def orders_get(self, **kwargs):
        return ()


def test_live_snapshot_contains_read_only_position_details(tmp_path: Path) -> None:
    profile = SimpleNamespace(
        profile_id="P1", symbol="GOLD#", enabled=True, login=12340369,
        server="XMGlobal-MT5 6", mt5_terminal="terminal64.exe",
        runtime_directory=str(tmp_path / "runtime/profiles/p1"),
    )
    account = SimpleNamespace(
        login=12340369, server="XMGlobal-MT5 6", currency="USD",
        balance=100.0, equity=107.9, margin=4.0, margin_free=103.9,
        profit=7.9, trade_allowed=True,
    )
    payload = publish_live_mt5_snapshot(profile=profile, mt5=MT5Stub(), account=account)
    assert payload["positions_total"] == 1
    assert payload["position_tickets"] == [1001]
    assert payload["positions"][0]["type"] == "SELL"
    assert payload["positions"][0]["sl"] == 4071.3
    assert payload["execution_authority"] is False
    assert payload["order_send_called"] is False


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_contract_reconciles_live_position_and_verifies_snapshot(tmp_path: Path) -> None:
    _write(tmp_path / "config/four_profile_demo.json", {
        "profiles": [{
            "profile_id": "P1", "profile_name": "Conservative", "runtime_directory": "runtime/profiles/p1",
            "maximum_units": 3, "sizing_authority": "CAPITAL_TIER_FORMULA_ONLY",
        }]
    })
    _write(tmp_path / "runtime/final_integration_status.json", {
        "trading_runtime": {"profiles": [{"profile_id": "P1", "runtime_state": "RUNNING"}]}
    })
    _write(tmp_path / "runtime/profiles/p1/status.json", {"runtime_state": "RUNNING"})
    _write(tmp_path / "runtime/profiles/p1/mt5_health.json", {"connection_status": "CONNECTED", "process_alive": True})
    _write(tmp_path / "runtime/profiles/p1/demo_execution_state.json", {
        "demo_gateway_status": "WAITING", "demo_gateway_reason": "waiting_for_runtime_evidence", "plan_id": "PLAN-1",
        "tickets": [1001], "sent_units": 1, "decision_action": "SELL", "decision_confidence": 100,
    })
    _write(tmp_path / "runtime/profiles/p1/mt5_live_snapshot.json", {
        "producer": "DemoExecutionGatewayExistingSession", "profile_id": "P1",
        "connection_status": "CONNECTED", "process_alive": True, "evidence_kind": "LIVE",
        "monitoring_mode": "EXISTING_RUNTIME_SESSION_READ_ONLY", "tick_available": True,
        "balance": 100.0, "equity": 107.9, "free_margin": 103.9, "margin": 4.0,
        "floating_profit": 7.9, "bid": 4042.1, "ask": 4042.4,
        "positions_total": 1, "orders_total": 0, "position_snapshot_available": True,
        "positions": [{"ticket": 1001, "type": "SELL", "price_open": 4050.0,
                       "price_current": 4042.1, "sl": 4071.3, "tp": 4007.4, "profit": 7.9}],
        "position_tickets": [1001],
    })
    contract = build_dashboard_contract(tmp_path)
    row = contract["profiles"][0]
    assert row["verified_snapshot"] is True
    assert row["open_position_observed"] is True
    assert row["position_tickets"] == [1001]
    assert row["position_execution_link"] == "MATCHED_LAST_EXECUTION"
    assert row["trade_plan_id"] == "PLAN-1"
    assert row["stop_loss"] == 4071.3
    assert row["take_profit"] == 4007.4

    html = ThreeDashboardRuntime().render_profiles_html({"profiles": contract["profiles"], "project_root": tmp_path})
    assert "Verified snapshot" in html
    assert ">1/4<" in html
    assert "PLAN-1" in html
    assert "4071.3 / 4007.4" in html
    assert "current 1001" in html


def test_current_market_and_gateway_reason_use_fresh_evidence() -> None:
    result = normalize_profile_state({
        "runtime_state": "RUNNING", "connection_status": "CONNECTED",
        "demo_gateway_status": "WAITING", "demo_gateway_reason": "waiting_for_runtime_evidence",
        "bid": 4042.1, "ask": 4042.4, "tick_available": True, "evidence_kind": "LIVE",
        "source_metadata": {
            "profile_status": {"fresh": True}, "runtime_authority": {"fresh": True},
            "mt5_health": {"fresh": True, "exists": True},
            "execution_state": {"fresh": True, "exists": True},
        },
    })
    assert result["market_current"] == "OPEN_TICKING"
    assert result["market_current_source"] == "LIVE_TICK_EVIDENCE"
    assert result["current_reason"] == "waiting_for_next_runtime_cycle"
