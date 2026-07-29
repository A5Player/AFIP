from pathlib import Path
from types import SimpleNamespace

from afip.production_activation_runtime import ProductionActivationRuntime


def _runtime(tmp_path: Path):
    profile = SimpleNamespace(profile_id="P1", symbol="GOLD#")
    policy = SimpleNamespace(maximum_units=3, minimum_seconds_between_entries=900, magic=26071001)
    return ProductionActivationRuntime(profile=profile, policy=policy, runtime_root=tmp_path)


def test_complete_plan_is_built_from_canonical_lot_authority(tmp_path):
    runtime = _runtime(tmp_path)
    authority = SimpleNamespace(
        approved_lots=(0.01,), approved_units=1,
        as_dict=lambda: {"approved_lots": [0.01], "approved_units": 1, "source": "SINGLE_LOT_AUTHORITY"},
    )
    simulation = {
        "decision": {"action": "BUY", "confidence": 99.0},
        "modular_intelligence": {
            "market_regime": {"regime": "TREND"},
            "pattern": {"pattern_name": "TEST_PATTERN", "family": "TREND"},
        },
        "trading_cost_intelligence": {"max_spread_points": 35.0},
    }
    account = {"balance": 100.0, "equity": 100.0, "margin_free": 90.0}
    requests = [{"symbol": "GOLD#", "price": 3300.0, "sl": 3290.0, "tp": 3320.0, "deviation": 20}]
    plan, cert = runtime.build_and_certify_plan(
        simulation=simulation, account=account, authority=authority,
        action="BUY", confidence=99.0, prepared_requests=requests,
        execution_trace_id="TRACE-1",
    )
    assert cert.certified is True
    assert cert.allowed_units == 1
    assert plan.capital.capital_per_unit == 0.0
    assert (tmp_path / "profiles" / "p1" / "production_activation" / "status.json").exists()


def test_plan_certification_blocks_missing_protection(tmp_path):
    runtime = _runtime(tmp_path)
    authority = SimpleNamespace(
        approved_lots=(0.01,), approved_units=1,
        as_dict=lambda: {"approved_lots": [0.01], "approved_units": 1},
    )
    plan, cert = runtime.build_and_certify_plan(
        simulation={"decision": {"action": "BUY"}, "trading_cost_intelligence": {"max_spread_points": 35}},
        account={"balance": 10, "equity": 10, "margin_free": 10}, authority=authority,
        action="BUY", confidence=99, prepared_requests=[{"symbol":"GOLD#","price":3300,"sl":0,"tp":3320,"deviation":20}],
        execution_trace_id="TRACE-2",
    )
    assert cert.certified is False
    assert "protective_stop_missing" in cert.rejection_reasons


def test_position_observer_is_connected_even_with_no_positions(tmp_path):
    runtime = _runtime(tmp_path)
    result = runtime.observe_positions(mt5=SimpleNamespace(), positions=[])
    assert result["status"] == "ACTIVE"
    assert result["positions_evaluated"] == 0
