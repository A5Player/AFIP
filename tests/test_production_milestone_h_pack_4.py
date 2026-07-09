"""Production Milestone H Pack 4 tests."""

from afip.dashboard_center import DashboardRuntimeStatus
from afip.runtime_service_manager import RuntimeEventLogger, RuntimeRecoveryEngine, RuntimeServiceManager


def test_runtime_service_manager_reports_ready_vps_runtime_without_live_execution():
    report = RuntimeServiceManager().evaluate_one({"execution_mode": "LOCKED_SIMULATION_ONLY", "runtime_seconds": 3600, "heartbeat_age_seconds": 5})
    assert report.status == "READY"
    assert report.runtime_gate == "RUNTIME_SERVICE_READY"
    assert report.trading_status == "RUNNING"
    assert report.live_execution_enabled is False
    assert "heartbeat" in report.dashboard_sections


def test_runtime_service_blocks_live_execution_policy():
    report = RuntimeServiceManager().evaluate_one({"execution_mode": "LIVE"})
    assert report.status == "BLOCKED"
    assert report.trading_status == "PAUSED"
    assert report.waiting_reason == "safe_execution_mode_required"
    assert report.expected_next_action == "switch_to_simulation_or_paper"


def test_recovery_engine_explains_internet_disconnect_flow():
    report = RuntimeRecoveryEngine().evaluate_one({"internet_status": "DISCONNECTED"})
    assert report.status == "RECOVERING"
    assert report.trading_status == "PAUSED"
    assert report.recovery_steps == ("pause_trading", "wait_for_internet", "recheck_mt5", "recheck_broker")
    assert report.waiting_reason == "internet_disconnected"


def test_recovery_engine_explains_mt5_and_broker_validation_before_resume():
    mt5 = RuntimeRecoveryEngine().evaluate_one({"mt5_status": "DISCONNECTED"})
    broker = RuntimeRecoveryEngine().evaluate_one({"broker_status": "OFFLINE"})
    assert "reconnect_mt5" in mt5.recovery_steps
    assert "validate_xm_broker" in broker.recovery_steps
    assert mt5.expected_next_action == "reconnect_mt5"
    assert broker.expected_next_action == "validate_broker_connection"


def test_runtime_watchdog_reviews_stale_heartbeat_and_resource_pressure():
    heartbeat = RuntimeServiceManager().evaluate_one({"heartbeat_age_seconds": 120})
    resource = RuntimeServiceManager().evaluate_one({"cpu_percent": 96})
    assert heartbeat.status == "REVIEW"
    assert heartbeat.reason == "runtime_heartbeat_stale"
    assert resource.status == "REVIEW"
    assert resource.reason == "runtime_watchdog_review"


def test_event_logger_creates_dashboard_timeline_with_thai_and_english_messages():
    events = RuntimeEventLogger().build([
        {"event_name": "runtime_started", "status": "INFO", "reason": "started", "action": "observe_runtime"},
        {"event_name": "internet_lost", "status": "WARNING", "reason": "offline", "action": "pause_trading"},
        {"event_name": "mt5_reconnected", "status": "INFO", "reason": "connected", "action": "validate_broker"},
    ])
    assert [event.sequence for event in events] == [1, 2, 3]
    assert events[1].dashboard_message_th
    assert events[1].dashboard_message_en
    assert events[1].action == "pause_trading"


def test_dashboard_runtime_composes_runtime_service_dependency():
    ready = DashboardRuntimeStatus().evaluate_one({"execution_mode": "LOCKED_SIMULATION_ONLY"})
    recovering = DashboardRuntimeStatus().evaluate_one({"internet_status": "DISCONNECTED", "market_regime": "TRENDING", "signal_context": "runtime_review"})
    assert ready.runtime_service_status == "READY"
    assert ready.live_execution_enabled is False
    assert recovering.runtime_service_status == "RECOVERING"
    assert recovering.status == "WAITING"
