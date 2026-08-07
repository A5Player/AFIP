from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from afip.demo_execution_gateway.runtime import DemoExecutionGateway, DemoProfilePolicy
from afip.four_profile_operations.runtime import ProfileOperationalConfig


def _profile(tmp_path: Path) -> ProfileOperationalConfig:
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


def _policy() -> DemoProfilePolicy:
    return DemoProfilePolicy.from_mapping({
        "profile_id": "P1", "enabled": True, "execution_enabled": True,
        "demo_execution_enabled": True, "maximum_units": 3,
        "minimum_confidence": 98, "minimum_seconds_between_entries": 900,
        "magic": 26071001, "lot_per_unit": 0.01,
        "allocation_mode": "CAPITAL_TIER_TABLE", "maximum_concurrent_orders": 3,
        "maximum_lot_per_order": 0.01,
        "capital_tiers": [{"minimum_balance": 0, "lots": [0.01, 0.01, 0.01]}],
    })


def _simulation() -> dict:
    return {
        "data_status": "READY", "data_source": "MT5_MULTI_TIMEFRAME_H1",
        "decision": {"action": "BUY", "confidence": 100},
        "risk": {"allowed": True},
        "trading_cost_intelligence": {
            "status": "PASS", "allowed": True, "spread_points": 20.0,
            "caution_spread_points": 25.0, "max_spread_points": 35.0,
        },
        "order": {
            "status": "SIMULATION_ORDER_READY", "action": "BUY",
            "unit_allocation": {"requested_units": 3},
            "protection": {"stop_loss_points": 3000, "take_profit_points": 500},
        },
    }


class BatchCheckMT5:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    ORDER_TIME_GTC = 0
    ORDER_FILLING_IOC = 1
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_PLACED = 10008
    TRADE_RETCODE_DONE_PARTIAL = 10010

    def __init__(self, failing_check_number: int | None = None) -> None:
        self.failing_check_number = failing_check_number
        self.checks: list[dict] = []
        self.sent: list[dict] = []

    def initialize(self, *args, **kwargs): return True
    def shutdown(self): return None
    def last_error(self): return (0, "OK")
    def account_info(self):
        return SimpleNamespace(
            login=1301760369, server="XMGlobal-MT5 6", trade_mode=0,
            trade_allowed=True, trade_expert=True, balance=3000.0, equity=3000.0,
        )
    def terminal_info(self): return SimpleNamespace(connected=True)
    def symbol_select(self, symbol, enable): return True
    def symbol_info(self, symbol): return SimpleNamespace(point=0.01, digits=2)
    def symbol_info_tick(self, symbol): return SimpleNamespace(ask=2400.20, bid=2400.00)
    def positions_get(self, **kwargs): return ()
    def order_check(self, request):
        self.checks.append(dict(request))
        if self.failing_check_number == len(self.checks):
            return SimpleNamespace(retcode=10013, comment="Invalid request")
        return SimpleNamespace(retcode=0, comment="Done")
    def order_send(self, request):
        self.sent.append(dict(request))
        return SimpleNamespace(retcode=10009, order=1000 + len(self.sent), deal=0, comment="Done")


def _arm(monkeypatch) -> None:
    monkeypatch.setenv("AFIP_P1_LOGIN", "1301760369")
    monkeypatch.setenv("AFIP_P1_PASSWORD", "secret")
    monkeypatch.setenv("AFIP_DEMO_EXECUTION_ARMED", "YES")
    monkeypatch.setenv("AFIP_P1_DEMO_ARMED", "YES")


def test_capacity_three_still_checks_and_sends_only_initial_leg(tmp_path, monkeypatch):
    _arm(monkeypatch)
    mt5 = BatchCheckMT5()
    report = DemoExecutionGateway(
        _profile(tmp_path), _policy(), mt5=mt5, simulate=_simulation,
    ).run_cycle()

    assert report.status == "ORDER_SENT"
    assert len(mt5.checks) == 1
    assert len(mt5.sent) == 1


def test_unused_reserved_legs_are_not_prechecked_or_sent(tmp_path, monkeypatch):
    _arm(monkeypatch)
    mt5 = BatchCheckMT5(failing_check_number=2)
    report = DemoExecutionGateway(
        _profile(tmp_path), _policy(), mt5=mt5, simulate=_simulation,
    ).run_cycle()

    assert report.status == "ORDER_SENT"
    assert report.order_check_called is True
    assert report.order_send_called is True
    assert len(mt5.checks) == 1
    assert len(mt5.sent) == 1
