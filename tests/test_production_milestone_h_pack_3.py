from afip.connection_manager import ConnectionManagerRuntime
from afip.dashboard_center import DashboardRuntimeStatus
from afip.historical_data_manager import HistoricalDataManagerRuntime
from afip.profile_manager import ProfileManagerRuntime, TradingProfile
from afip.setup_wizard import SetupWizardRuntime


def _record(**updates):
    data = {
        "market_regime": "TRENDING",
        "signal_context": "SELL_CONTINUATION",
        "execution_mode": "LOCKED_SIMULATION_ONLY",
        "broker": "XM",
        "symbol": "GOLD#",
        "login": "123456",
        "password": "secret",
        "mt5_terminal_path": "C:/Program Files/MetaTrader 5/terminal64.exe",
        "profile_name": "Conservative",
        "history_ready": True,
        "connection_test_passed": True,
        "saved": True,
        "requested_days": 365,
        "downloaded_bars": 8760,
        "missing_bars": 0,
        "duplicate_bars": 0,
        "internet_status": "CONNECTED",
        "mt5_status": "CONNECTED",
        "broker_status": "XM_READY",
        "market_status": "OPEN",
    }
    data.update(updates)
    return data


def test_profile_manager_keeps_profile_separate_from_account_and_mt5():
    report = ProfileManagerRuntime().evaluate_one(
        _record(
            profile={"profile_name": "Balanced", "maximum_units": 3, "split_orders": True, "broker": "XM", "symbol": "GOLD#"},
            account={"account_id": "xm_demo_100", "login": "456789", "server": "XMGlobal-MT5 6"},
            mt5={"path": "C:/MT5/terminal64.exe"},
        )
    )

    assert report.status == "READY"
    assert report.profile_gate == "PROFILE_MANAGER_READY"
    assert report.profile_architecture_valid is True
    assert report.assigned_account_id == "xm_demo_100"
    assert report.profile.profile_name == "Balanced"
    assert report.profile.order_lots == (0.01, 0.01, 0.01)
    assert report.profile.total_lot_exposure == 0.03
    assert report.login_mask == "****89"
    assert report.trading_logic_changed is False


def test_profile_manager_documents_every_setting_in_thai_and_english():
    profile = TradingProfile.from_mapping({"profile_name": "Research", "profile_type": "RESEARCH", "maximum_units": 1})

    assert profile.research_mode is True
    assert profile.broker == "XM"
    assert profile.symbol == "GOLD#"
    assert len(profile.documentation) >= 12
    assert all(item.documentation.thai_description for item in profile.documentation)
    assert all(item.documentation.english_description for item in profile.documentation)
    assert all(item.documentation.default_value != "" for item in profile.documentation)
    assert all(item.documentation.recommended_value != "" for item in profile.documentation)
    assert all(item.documentation.impact != "" for item in profile.documentation)


def test_profile_manager_blocks_live_execution_and_non_xm_gold_policy():
    live = ProfileManagerRuntime().evaluate_one(_record(execution_mode="LIVE"))
    review = ProfileManagerRuntime().evaluate_one(_record(profile={"profile_name": "Custom", "broker": "EXNESS", "symbol": "EURUSD", "maximum_units": 1}))

    assert live.status == "BLOCKED"
    assert live.reason == "live_execution_not_allowed_for_profile_manager"
    assert review.status == "REVIEW"
    assert "version1_xm_gold_only_required" in review.review_items


def test_setup_wizard_guides_required_steps_before_run_afip():
    waiting = SetupWizardRuntime().evaluate_one(_record(login="", history_ready=False, connection_test_passed=False, saved=False))
    ready = SetupWizardRuntime().evaluate_one(_record())

    assert waiting.status == "WAITING"
    assert waiting.next_step == "login"
    assert ready.status == "READY"
    assert ready.wizard_gate == "SETUP_WIZARD_READY"
    assert ready.can_save is True
    assert ready.can_run_afip is True
    assert [step.step_id for step in ready.steps] == ["welcome", "broker", "login", "mt5_path", "historical_data", "profile", "test_connection", "save"]


def test_connection_manager_displays_runtime_and_waiting_reason():
    ready = ConnectionManagerRuntime().evaluate_one(_record(cpu_percent=20, ram_percent=40, disk_percent=60, runtime_seconds=3600))
    waiting = ConnectionManagerRuntime().evaluate_one(_record(internet_status="DISCONNECTED", internet_disconnect_count=2, internet_disconnect_duration_seconds=120, reconnect_count=1))

    assert ready.status == "READY"
    assert ready.connection_gate == "CONNECTION_MANAGER_READY"
    assert ready.profile_name == "Conservative"
    assert ready.runtime_seconds == 3600
    assert waiting.status == "WAITING"
    assert waiting.waiting_reason == "internet_disconnected"
    assert waiting.internet_disconnect_count == 2
    assert waiting.reconnect_count == 1


def test_historical_data_manager_validates_missing_bars_and_walk_forward():
    ready = HistoricalDataManagerRuntime().evaluate_one(_record(downloaded_bars=9000, requested_days=365))
    review = HistoricalDataManagerRuntime().evaluate_one(_record(downloaded_bars=9000, requested_days=365, missing_bars=10))

    assert ready.status == "READY"
    assert ready.walk_forward_ready is True
    assert ready.research_ready is True
    assert ready.quality_score == 100.0
    assert review.status == "REVIEW"
    assert review.walk_forward_ready is False
    assert "missing_bars_detected" in review.validation_items


def test_dashboard_runtime_composes_pack_3_managers_and_explainability_sections():
    report = DashboardRuntimeStatus().evaluate_one(_record(downloaded_bars=9000))

    assert report.status == "READY"
    assert report.dashboard_runtime_gate == "DASHBOARD_RUNTIME_READY"
    assert report.profile_status == "READY"
    assert report.setup_status == "READY"
    assert report.connection_status == "READY"
    assert report.historical_data_status == "READY"
    assert "runtime" in report.dashboard_sections
    assert "afip_bank" in report.dashboard_sections
    assert "holding" in report.decision_explainability_sections
    assert "stop_loss_move" in report.decision_explainability_sections
    assert "order_quality" in report.order_center_sections
