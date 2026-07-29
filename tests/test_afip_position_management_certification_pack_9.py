from pathlib import Path
from types import SimpleNamespace

from afip.position_care_runtime import PositionCareSnapshot, PositionCareSupervisor
from afip.production_activation_runtime import ProductionActivationRuntime


def runtime(tmp_path: Path) -> ProductionActivationRuntime:
    profile = SimpleNamespace(profile_id="P1", symbol="GOLD#")
    policy = SimpleNamespace(magic=1001)
    return ProductionActivationRuntime(profile=profile, policy=policy, runtime_root=tmp_path)


def snapshot(**overrides):
    data = dict(
        snapshot_id="S1", plan_id="PLAN-1", profile_id="P1", symbol="GOLD#", ticket="1",
        direction="BUY", entry_price=2400.0, current_price=2410.0,
        initial_stop_price=2390.0, current_stop_price=2400.0, current_take_profit_price=2420.0,
        volume_lots=0.01, unrealized_profit=10.0, favorable_points=1000.0, adverse_points=0.0,
        holding_seconds=60, market_regime_valid=True, thesis_valid=True, structure_valid=True,
        volatility_acceptable=True, liquidity_acceptable=True, market_data_fresh=True,
        connection_ready=True, account_state_reconciled=True, break_even_triggered=True,
        trailing_triggered=True, partial_close_triggered=False, target_reached=False,
        hard_invalidation_reached=False, emergency_condition_active=False,
        observed_at="2026-07-29T00:00:00+00:00",
    )
    data.update(overrides)
    return PositionCareSnapshot(**data)


def test_trailing_stop_uses_price_domain_not_broker_points():
    proposed = PositionCareSupervisor._profit_protective_stop(snapshot())
    assert proposed == 2405.0
    assert proposed < 2410.0


def test_sell_trailing_stop_uses_price_domain():
    snap = snapshot(direction="SELL", entry_price=2400.0, current_price=2390.0,
                    current_stop_price=2400.0, favorable_points=1000.0)
    assert PositionCareSupervisor._profit_protective_stop(snap) == 2395.0


class MT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    POSITION_TYPE_BUY = 0
    TRADE_ACTION_SLTP = 6
    TRADE_RETCODE_DONE = 10009
    def __init__(self, trade_mode=0):
        self.trade_mode = trade_mode
        self.checked = []
        self.sent = []
    def account_info(self): return SimpleNamespace(trade_mode=self.trade_mode)
    def symbol_info(self, symbol): return SimpleNamespace(point=0.01)
    def order_check(self, request):
        self.checked.append(request)
        return SimpleNamespace(retcode=0, comment="ok")
    def order_send(self, request):
        self.sent.append(request)
        return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, comment="done")
    def last_error(self): return (0, "ok")


def position(**overrides):
    data = dict(ticket=77, type=0, price_current=2410.0, price_open=2400.0, sl=2400.0, tp=2420.0)
    data.update(overrides)
    return SimpleNamespace(**data)


def decision(stop=2405.0):
    return SimpleNamespace(recommended_action="RECOMMEND_TRAILING_STOP_UPDATE", proposed_stop_price=stop)


def test_sltp_is_demo_only(tmp_path):
    mt5 = MT5(trade_mode=1)
    result = runtime(tmp_path)._execute_position_action(mt5=mt5, position=position(), decision=decision())
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "demo_account_not_verified"
    assert not mt5.checked and not mt5.sent


def test_duplicate_or_non_improving_stop_is_not_sent(tmp_path):
    mt5 = MT5()
    result = runtime(tmp_path)._execute_position_action(mt5=mt5, position=position(sl=2405.0), decision=decision(2405.0))
    assert result["status"] == "NO_CHANGE"
    assert result["reason"] == "stop_not_improved"
    assert not mt5.checked and not mt5.sent


def test_stop_crossing_market_is_blocked(tmp_path):
    mt5 = MT5()
    result = runtime(tmp_path)._execute_position_action(mt5=mt5, position=position(), decision=decision(2410.0))
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "buy_stop_crosses_market"
    assert not mt5.checked and not mt5.sent


def test_valid_demo_stop_improvement_is_checked_then_sent(tmp_path):
    mt5 = MT5()
    result = runtime(tmp_path)._execute_position_action(mt5=mt5, position=position(), decision=decision(2405.0))
    assert result["status"] == "EXECUTED"
    assert result["order_check_called"] is True
    assert result["order_send_called"] is True
    assert len(mt5.checked) == len(mt5.sent) == 1


def test_position_management_policy_is_explicit_in_source():
    source = Path("afip/production_activation_runtime/runtime.py").read_text(encoding="utf-8")
    assert '"partial_close": "DISABLED_UNTIL_EXPLICIT_CERTIFIED_TRIGGER"' in source
    assert '"pyramiding": "NO_ADDITIONAL_UNITS_OUTSIDE_ORIGINAL_CERTIFIED_PLAN"' in source
    assert '"automatic_full_close": "NOT_ENABLED_BY_THIS_BRIDGE"' in source
