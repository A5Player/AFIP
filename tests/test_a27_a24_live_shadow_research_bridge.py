from pathlib import Path
from types import SimpleNamespace

from afip.position_care_runtime import PositionCareSnapshot
from afip.production_activation_runtime import ProductionActivationRuntime


class ClosedBarMT5:
    TIMEFRAME_H1 = 60

    def __init__(self) -> None:
        self.calls = []
        self.order_check_calls = 0
        self.order_send_calls = 0

    def symbol_info(self, symbol):
        return SimpleNamespace(point=0.01, spread=12)

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        self.calls.append((symbol, timeframe, start_pos, count))
        return [
            {"time": 1_700_000_000 + index * 3600, "open": 100 + index * .1,
             "high": 100.2 + index * .1, "low": 99.9 + index * .1,
             "close": 100.1 + index * .1, "tick_volume": 100 + index}
            for index in range(21)
        ]

    def order_check(self, request):
        self.order_check_calls += 1

    def order_send(self, request):
        self.order_send_calls += 1


def _runtime(tmp_path: Path) -> ProductionActivationRuntime:
    return ProductionActivationRuntime(
        profile=SimpleNamespace(profile_id="P4", symbol="GOLD#"),
        policy=SimpleNamespace(magic=26071004), runtime_root=tmp_path / "runtime",
    )


def _snapshot() -> PositionCareSnapshot:
    return PositionCareSnapshot(
        snapshot_id="PCS-1", plan_id="PLAN-1", profile_id="P4", symbol="GOLD#",
        ticket="123", direction="BUY", entry_price=100, current_price=101.9,
        initial_stop_price=99, current_stop_price=100, current_take_profit_price=102,
        volume_lots=.01, unrealized_profit=1, favorable_points=190, adverse_points=0,
        holding_seconds=7200, market_regime_valid=True, thesis_valid=True,
        structure_valid=True, volatility_acceptable=True, liquidity_acceptable=True,
        market_data_fresh=True, connection_ready=True, account_state_reconciled=True,
        break_even_triggered=True, trailing_triggered=True, partial_close_triggered=False,
        target_reached=False, hard_invalidation_reached=False,
        emergency_condition_active=False, observed_at="2026-08-14T00:00:00+00:00",
    )


def test_live_shadow_bridge_reads_closed_h1_and_never_calls_order_api(tmp_path):
    runtime = _runtime(tmp_path)
    mt5 = ClosedBarMT5()
    result = runtime._observe_a24_tp_volume(
        mt5=mt5, position=SimpleNamespace(), plan=SimpleNamespace(plan_id="PLAN-1"),
        plan_payload={"tickets": [123]}, snapshot=_snapshot(), risk_points=100,
        intelligence={"modular_intelligence": {"market_regime": {"regime": "TREND"}}},
    )
    assert result["status"] == "RECORDED"
    assert result["research_only"] is True and result["execution_authority"] == "NONE"
    assert mt5.calls == [("GOLD#", 60, 1, 21)]
    assert mt5.order_check_calls == 0 and mt5.order_send_calls == 0
    assert runtime.a24_research.dataset.verify("a24_tp_volume_decisions")


def test_same_closed_bar_is_suppressed_instead_of_rewritten(tmp_path):
    runtime = _runtime(tmp_path)
    mt5 = ClosedBarMT5()
    kwargs = dict(
        mt5=mt5, position=SimpleNamespace(), plan=SimpleNamespace(plan_id="PLAN-1"),
        plan_payload={"tickets": [123]}, snapshot=_snapshot(), risk_points=100,
        intelligence={},
    )
    assert runtime._observe_a24_tp_volume(**kwargs)["status"] == "RECORDED"
    assert runtime._observe_a24_tp_volume(**kwargs)["status"] == "DUPLICATE_SUPPRESSED"
    assert runtime.a24_research.dataset.count("a24_tp_volume_decisions") == 1


def test_missing_closed_bar_reader_fails_closed_without_order_authority(tmp_path):
    result = _runtime(tmp_path)._observe_a24_tp_volume(
        mt5=SimpleNamespace(symbol_info=lambda symbol: SimpleNamespace(point=.01)),
        position=SimpleNamespace(), plan=SimpleNamespace(plan_id="PLAN-1"),
        plan_payload={"tickets": [123]}, snapshot=_snapshot(), risk_points=100,
        intelligence={},
    )
    assert result["status"] == "DATA_UNAVAILABLE"
    assert result["execution_authority"] == "NONE" and result["no_order_sent"] is True
