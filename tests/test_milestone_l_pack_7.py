from afip.dashboard_ui import DashboardUIRuntime
from afip.shadow_execution_observation import ShadowExecutionObservationRuntime


def _record(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "performance_certification_status": "READY", "performance_certification_id": "L06-ABC",
        "certified_for_shadow_observation": True, "decision_id": "L03-ABC",
        "approved_action": "ENTRY", "position_state": "FLAT", "direction": "BUY", "requested_units": 1,
        "intended_entry_price": 2400.0, "observed_market_price": 2400.2,
        "intended_stop_loss": 2395.0, "intended_take_profit": 2410.0,
        "observed_spread_points": 30.0, "maximum_spread_points": 80.0,
        "observed_latency_ms": 120.0, "maximum_latency_ms": 500.0,
        "market_data_fresh": True, "market_session_open": True,
        "risk_validation_valid": True, "timing_validation_valid": True,
        "market_structure_confirmed": True, "independent_trade_plan_valid": True,
        "protected_runner_exposure_included": True,
        "traditional_dca_enabled": False, "averaging_down_enabled": False,
        "execution_status": "LOCKED_SIMULATION_ONLY", "direct_execution": False,
        "live_execution_enabled": False, "order_status": "NO_ORDER_SENT",
        "broker_request_created": False, "order_transmission_attempted": False,
    }
    record.update(extra)
    return record


def test_shadow_observation_is_ready_without_order_transmission():
    report = ShadowExecutionObservationRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.shadow_instruction_created is True
    assert report.broker_request_created is False
    assert report.order_status == "NO_ORDER_SENT"


def test_shadow_observation_id_is_deterministic():
    runtime = ShadowExecutionObservationRuntime()
    assert runtime.evaluate_one(_record()).shadow_observation_id == runtime.evaluate_one(_record()).shadow_observation_id


def test_pack6_certification_and_decision_link_are_required():
    runtime = ShadowExecutionObservationRuntime()
    assert "performance_certification_not_ready" in runtime.evaluate_one(_record(performance_certification_status="BLOCKED")).block_reasons
    assert "performance_certification_id_missing" in runtime.evaluate_one(_record(performance_certification_id="")).block_reasons
    assert "decision_id_missing" in runtime.evaluate_one(_record(decision_id="")).block_reasons


def test_market_quality_gates_are_enforced():
    runtime = ShadowExecutionObservationRuntime()
    assert "market_data_stale" in runtime.evaluate_one(_record(market_data_fresh=False)).block_reasons
    assert "spread_above_limit" in runtime.evaluate_one(_record(observed_spread_points=100.0)).block_reasons
    assert "latency_above_limit" in runtime.evaluate_one(_record(observed_latency_ms=700.0)).block_reasons


def test_buy_sell_geometry_is_validated():
    runtime = ShadowExecutionObservationRuntime()
    assert "action_geometry_invalid" in runtime.evaluate_one(_record(intended_stop_loss=2405.0)).block_reasons
    sell = _record(direction="SELL", intended_stop_loss=2410.0, intended_take_profit=2390.0)
    assert runtime.evaluate_one(sell).status == "READY"


def test_no_dca_runner_exposure_and_execution_locks_are_enforced():
    runtime = ShadowExecutionObservationRuntime()
    assert "traditional_dca_enabled" in runtime.evaluate_one(_record(traditional_dca_enabled=True)).block_reasons
    assert "protected_runner_exposure_excluded" in runtime.evaluate_one(_record(protected_runner_exposure_included=False)).block_reasons
    assert "order_transmission_attempted" in runtime.evaluate_one(_record(order_transmission_attempted=True)).block_reasons


def test_dashboard_contains_shadow_execution_observation_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "shadow_execution_observation" in {panel.panel_id for panel in dashboard.panels}
