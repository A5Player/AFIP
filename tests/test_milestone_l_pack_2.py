from afip.dashboard_ui import DashboardUIRuntime
from afip.paper_execution_session import PaperExecutionSessionRuntime


def _record(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "paper_execution_foundation_status": "READY", "paper_account_connected": True,
        "market_session_available": True, "market_data_fresh": True,
        "spread_points": 25.0, "maximum_spread_points": 80.0,
        "latency_ms": 90.0, "maximum_latency_ms": 1000.0,
        "data_age_seconds": 2.0, "maximum_data_age_seconds": 120.0,
        "clock_sync_valid": True, "risk_limits_valid": True, "audit_record_ready": True,
        "independent_trade_plan_required": True, "traditional_dca_enabled": False,
        "averaging_down_enabled": False, "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT", "direct_execution": False, "live_execution_enabled": False,
    }
    record.update(extra)
    return record


def test_paper_execution_session_ready():
    report = PaperExecutionSessionRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.session_readiness == "PAPER_SESSION_READY"
    assert report.order_status == "NO_ORDER_SENT"


def test_observation_id_is_deterministic():
    runtime = PaperExecutionSessionRuntime()
    assert runtime.evaluate_one(_record()).observation_id == runtime.evaluate_one(_record()).observation_id


def test_data_spread_and_latency_are_certified():
    runtime = PaperExecutionSessionRuntime()
    assert "market_data_stale" in runtime.evaluate_one(_record(data_age_seconds=121.0)).block_reasons
    assert "spread_above_limit" in runtime.evaluate_one(_record(spread_points=81.0)).block_reasons
    assert "latency_above_limit" in runtime.evaluate_one(_record(latency_ms=1001.0)).block_reasons


def test_session_risk_clock_and_audit_are_required():
    runtime = PaperExecutionSessionRuntime()
    assert "market_session_not_available" in runtime.evaluate_one(_record(market_session_available=False)).block_reasons
    assert "clock_not_synchronized" in runtime.evaluate_one(_record(clock_sync_valid=False)).block_reasons
    assert "risk_limits_invalid" in runtime.evaluate_one(_record(risk_limits_valid=False)).block_reasons
    assert "audit_record_not_ready" in runtime.evaluate_one(_record(audit_record_ready=False)).block_reasons


def test_dca_and_averaging_down_are_disabled():
    runtime = PaperExecutionSessionRuntime()
    assert "traditional_dca_enabled" in runtime.evaluate_one(_record(traditional_dca_enabled=True)).block_reasons
    assert "averaging_down_enabled" in runtime.evaluate_one(_record(averaging_down_enabled=True)).block_reasons


def test_policy_and_execution_locks_are_enforced():
    runtime = PaperExecutionSessionRuntime()
    assert "xm_only_policy" in runtime.evaluate_one(_record(broker="OTHER")).block_reasons
    assert "gold_only_policy" in runtime.evaluate_one(_record(symbol="XAUUSD")).block_reasons
    assert "live_execution_requested" in runtime.evaluate_one(_record(live_execution_enabled=True)).block_reasons


def test_dashboard_contains_paper_execution_session_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "paper_execution_session" in {panel.panel_id for panel in dashboard.panels}
