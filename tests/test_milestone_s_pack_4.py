from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from afip.demo_execution_gateway.runtime import DemoExecutionGateway, DemoProfilePolicy
from afip.four_profile_operations.runtime import ProfileOperationalConfig


def profile(tmp_path: Path) -> ProfileOperationalConfig:
    terminal = tmp_path / "terminal64.exe"
    terminal.write_text("", encoding="utf-8")
    return ProfileOperationalConfig(
        profile_id="P1", profile_name="High Safety", enabled=True, launch_mt5=False,
        mt5_folder=tmp_path, mt5_terminal=terminal, broker="XM", server="XMGlobal-MT5 6",
        symbol="GOLD#", login_env="AFIP_P1_LOGIN", password_env="AFIP_P1_PASSWORD",
        runtime_directory=tmp_path / "runtime", database_path=tmp_path / "database" / "afip.sqlite3",
        logs_directory=tmp_path / "logs", dashboard_path=tmp_path / "dashboard" / "index.html",
        learning_directory=tmp_path / "learning", knowledge_directory=tmp_path / "knowledge",
        statistics_directory=tmp_path / "statistics",
    )


def policy(**overrides):
    raw = dict(profile_id="P1", enabled=True, demo_execution_enabled=True, capital_per_unit=1000,
               maximum_units=3, minimum_confidence=98, minimum_seconds_between_entries=900,
               magic=26071001, lot_per_unit=0.01)
    raw.update(overrides)
    return DemoProfilePolicy.from_mapping(raw)


def simulation(data_status="READY", action="BUY", confidence=100):
    return {
        "data_status": data_status, "data_source": "MT5_MULTI_TIMEFRAME_H1",
        "decision": {"action": action, "confidence": confidence},
        "risk": {"allowed": True},
        "trading_cost_intelligence": {
            "status": "PASS", "allowed": True, "spread_points": 20.0,
            "caution_spread_points": 25.0, "max_spread_points": 35.0,
        },
        "order": {"status": "SIMULATION_ORDER_READY", "action": action,
                  "protection": {"stop_loss_points": 3000, "take_profit_points": 500}},
    }


class FakeMT5:
    ORDER_TYPE_BUY=0; ORDER_TYPE_SELL=1; TRADE_ACTION_DEAL=1; ORDER_TIME_GTC=0; ORDER_FILLING_IOC=1
    TRADE_RETCODE_DONE=10009; TRADE_RETCODE_PLACED=10008; TRADE_RETCODE_DONE_PARTIAL=10010
    def __init__(self, *, trade_mode=0, positions=()):
        self.trade_mode=trade_mode; self.positions=positions; self.sent=[]; self.shutdown_called=False
    def initialize(self, *a, **k): return True
    def shutdown(self): self.shutdown_called=True
    def last_error(self): return (0,"OK")
    def account_info(self):
        return SimpleNamespace(login=1301760369, server="XMGlobal-MT5 6", trade_mode=self.trade_mode,
                               trade_allowed=True, trade_expert=True, balance=3000.0)
    def terminal_info(self): return SimpleNamespace(connected=True)
    def symbol_select(self, symbol, enable): return True
    def symbol_info(self, symbol): return SimpleNamespace(point=0.01,digits=2)
    def symbol_info_tick(self, symbol): return SimpleNamespace(ask=2400.20,bid=2400.00)
    def positions_get(self, **kwargs): return self.positions
    def order_check(self, request): return SimpleNamespace(retcode=0,comment="Done")
    def order_send(self, request):
        self.sent.append(dict(request)); return SimpleNamespace(retcode=10009,order=1000+len(self.sent),deal=0,comment="Done")


def arm(monkeypatch):
    monkeypatch.setenv("AFIP_P1_LOGIN","1301760369")
    monkeypatch.setenv("AFIP_P1_PASSWORD","secret")
    monkeypatch.setenv("AFIP_DEMO_EXECUTION_ARMED","YES")
    monkeypatch.setenv("AFIP_P1_DEMO_ARMED","YES")


def test_policy_keeps_fixed_001_units():
    assert policy().validate() == ()
    assert "lot_per_unit_must_remain_0_01" in policy(lot_per_unit=0.02).validate()


def test_unarmed_gateway_never_reaches_order_send(tmp_path, monkeypatch):
    for key in (
        "AFIP_DEMO_EXECUTION_ARMED",
        "AFIP_P1_DEMO_ARMED",
        "AFIP_P2_DEMO_ARMED",
        "AFIP_P3_DEMO_ARMED",
        "AFIP_P4_DEMO_ARMED",
    ):
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("AFIP_P1_LOGIN","1301760369")
    monkeypatch.setenv("AFIP_P1_PASSWORD","secret")
    mt5=FakeMT5()
    report=DemoExecutionGateway(profile(tmp_path),policy(),mt5=mt5,simulate=simulation).run_cycle()
    assert report.status=="BLOCKED" and report.reason=="local_demo_execution_not_armed" and mt5.sent==[]


def test_real_account_is_blocked_before_order_send(tmp_path, monkeypatch):
    arm(monkeypatch); mt5=FakeMT5(trade_mode=2)
    report=DemoExecutionGateway(profile(tmp_path),policy(),mt5=mt5,simulate=simulation).run_cycle()
    assert report.reason=="account_is_not_demo" and not report.demo_verified and mt5.sent==[]


def test_fallback_market_data_is_never_executed(tmp_path, monkeypatch):
    arm(monkeypatch); mt5=FakeMT5()
    report=DemoExecutionGateway(profile(tmp_path),policy(),mt5=mt5,simulate=lambda:simulation("FALLBACK_READY")).run_cycle()
    assert report.status=="WAITING" and report.reason=="simulation_fallback_data_blocked" and mt5.sent==[]


def test_manual_position_acts_as_operator_override(tmp_path, monkeypatch):
    arm(monkeypatch); mt5=FakeMT5(positions=(SimpleNamespace(magic=0),))
    report=DemoExecutionGateway(profile(tmp_path),policy(),mt5=mt5,simulate=simulation).run_cycle()
    assert report.reason=="manual_position_detected_operator_override" and mt5.sent==[]


def test_profile_confidence_gate_is_enforced(tmp_path, monkeypatch):
    arm(monkeypatch); mt5=FakeMT5()
    report=DemoExecutionGateway(profile(tmp_path),policy(),mt5=mt5,simulate=lambda:simulation(confidence=97)).run_cycle()
    assert report.reason=="profile_confidence_below_threshold" and mt5.sent==[]


def test_protected_demo_orders_are_split_into_fixed_units(tmp_path, monkeypatch):
    arm(monkeypatch); mt5=FakeMT5()
    report=DemoExecutionGateway(profile(tmp_path),policy(),mt5=mt5,simulate=simulation).run_cycle()
    assert report.status=="ORDER_SENT" and report.sent_units==3 and len(mt5.sent)==3
    assert all(x["volume"]==0.01 and x["sl"]>0 and x["tp"]>0 for x in mt5.sent)


def test_existing_afip_units_reduce_capacity(tmp_path, monkeypatch):
    arm(monkeypatch); mt5=FakeMT5(positions=(SimpleNamespace(magic=26071001),SimpleNamespace(magic=26071001)))
    report=DemoExecutionGateway(profile(tmp_path),policy(),mt5=mt5,simulate=simulation).run_cycle()
    assert report.sent_units==1 and len(mt5.sent)==1


def test_duplicate_signal_cooldown_blocks_repeat(tmp_path, monkeypatch):
    arm(monkeypatch); p=profile(tmp_path); mt5=FakeMT5()
    gateway=DemoExecutionGateway(p,policy(),mt5=mt5,simulate=simulation)
    assert gateway.run_cycle().status=="ORDER_SENT"
    mt5.positions=()
    second=gateway.run_cycle()
    assert second.reason=="duplicate_signal_cooldown_active" and len(mt5.sent)==3


def test_password_is_not_written_to_state_or_ledger(tmp_path, monkeypatch):
    arm(monkeypatch); p=profile(tmp_path); mt5=FakeMT5()
    DemoExecutionGateway(p,policy(),mt5=mt5,simulate=simulation).run_cycle()
    text=p.runtime_directory.joinpath("demo_execution_state.json").read_text(encoding="utf-8") + p.logs_directory.joinpath("demo_execution_ledger.jsonl").read_text(encoding="utf-8")
    assert "secret" not in text and "1301760369" not in text


def test_trading_cost_caution_is_allowed_by_contract(tmp_path, monkeypatch):
    arm(monkeypatch); mt5=FakeMT5()
    payload=simulation()
    payload["trading_cost_intelligence"] = {
        "status": "CAUTION", "allowed": True, "spread_points": 29.0,
        "caution_spread_points": 25.0, "max_spread_points": 35.0,
    }
    report=DemoExecutionGateway(profile(tmp_path),policy(),mt5=mt5,simulate=lambda:payload).run_cycle()
    assert report.status=="ORDER_SENT" and report.sent_units==3
    assert report.trading_cost_status=="CAUTION" and report.trading_cost_allowed is True
    assert report.spread_points==29.0 and report.max_spread_points==35.0
    assert report.point_size==0.01 and report.digits==2
    assert report.order_check_called and report.order_send_called


def test_trading_cost_block_remains_fail_closed(tmp_path, monkeypatch):
    arm(monkeypatch); mt5=FakeMT5()
    payload=simulation()
    payload["trading_cost_intelligence"] = {
        "status": "BLOCK", "allowed": False, "spread_points": 36.0,
        "caution_spread_points": 25.0, "max_spread_points": 35.0,
    }
    report=DemoExecutionGateway(profile(tmp_path),policy(),mt5=mt5,simulate=lambda:payload).run_cycle()
    assert report.status=="WAITING" and report.reason=="trading_cost_not_approved"
    assert not report.order_check_called and not report.order_send_called and mt5.sent==[]


def test_unknown_trading_cost_status_is_blocked(tmp_path, monkeypatch):
    arm(monkeypatch); mt5=FakeMT5()
    payload=simulation()
    payload["trading_cost_intelligence"] = {"status": "", "allowed": True}
    report=DemoExecutionGateway(profile(tmp_path),policy(),mt5=mt5,simulate=lambda:payload).run_cycle()
    assert report.status=="BLOCKED" and report.reason=="trading_cost_status_unknown"
    assert mt5.sent==[]
