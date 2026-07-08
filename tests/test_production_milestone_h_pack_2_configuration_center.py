from afip.configuration_center import BrokerAccountConfig, ConfigurationCenterRuntime, ConfigurationRepository


def _record(**updates):
    data = {
        "market_regime": "TRENDING",
        "signal_context": "SELL_CONTINUATION",
        "execution_mode": "LOCKED_SIMULATION_ONLY",
        "accounts": [
            {"account_id": "xm_demo_100", "broker": "XM", "account_name": "XM Demo 100", "account_type": "DEMO", "server": "XMGlobal-MT5 6", "login": "123456", "symbol": "GOLD#", "enabled": True},
            {"account_id": "xm_demo_1000", "broker": "XM", "account_name": "XM Demo 1000", "account_type": "DEMO", "server": "XMGlobal-MT5 6", "login": "654321", "symbol": "GOLD#", "enabled": True},
        ],
        "risk": {"lot_size": 0.01, "max_positions": 1, "max_daily_loss_percent": 2.0, "max_drawdown_percent": 10.0, "risk_mode": "CONSERVATIVE"},
        "walk_forward": {"enabled": True, "history_days": 365, "learning_enabled": True, "lookahead_protection": True},
        "dashboard": {"language": "TH", "refresh_seconds": 5, "theme": "DARK", "show_top10": True, "show_bilingual_names": True},
        "capital": {"base_currency": "USD", "initial_capital": 100, "deposits": 0, "withdrawals": 0, "monthly_target_percent": 5},
    }
    data.update(updates)
    return data


def test_configuration_center_blocks_records_without_market_regime():
    report = ConfigurationCenterRuntime().evaluate_one(_record(market_regime=""))

    assert report.status == "BLOCKED"
    assert report.reason == "market_regime_required"
    assert report.configuration_gate == "BLOCKED"


def test_configuration_center_blocks_live_execution_mode():
    report = ConfigurationCenterRuntime().evaluate_one(_record(execution_mode="LIVE"))

    assert report.status == "BLOCKED"
    assert report.reason == "live_execution_not_allowed_for_configuration_center"
    assert report.trading_logic_changed is False


def test_configuration_center_preserves_regime_before_signal_context():
    report = ConfigurationCenterRuntime().evaluate_one(_record(market_regime="sideway", signal_context="wait_for_confirmation"))

    assert report.market_regime == "SIDEWAY"
    assert report.signal_context == "WAIT_FOR_CONFIRMATION"
    assert report.status == "READY"


def test_configuration_center_supports_two_xm_demo_accounts():
    report = ConfigurationCenterRuntime().evaluate_one(_record())

    assert report.status == "READY"
    assert report.configuration_gate == "CONFIGURATION_CENTER_READY"
    assert report.enabled_accounts == 2
    assert report.accounts[0].account_id == "xm_demo_100"
    assert report.accounts[0].symbol == "GOLD#"
    assert report.accounts[0].login_mask.endswith("56")


def test_configuration_center_requires_review_for_missing_safe_sections():
    report = ConfigurationCenterRuntime().evaluate_one(_record(accounts=[{"enabled": False}], walk_forward={"enabled": True, "lookahead_protection": False}))

    assert report.status == "REVIEW"
    assert "enabled_broker_account_required" in report.review_items
    assert "walk_forward_lookahead_protection_required" in report.review_items


def test_configuration_center_report_and_repository_are_deterministic():
    repository = ConfigurationRepository(_record(risk={"lot_size": 0.01}))
    runtime = ConfigurationCenterRuntime(repository)
    report = runtime.explain_one({"market_regime": "TRENDING"})
    account = BrokerAccountConfig.from_mapping({"broker": "XM", "login": "987654", "enabled": True})

    assert report.as_dict()["trading_logic_changed"] is False
    assert report.as_dict()["all_sections_ready"] is True
    assert "Reason: configuration_center_ready" in report.as_text()
    assert account.status_icon == "🟢"
    assert account.login_mask == "****54"
