from afip.dashboard_center import DashboardRuntimeStatus
from afip.research_center import ResearchCenterRuntime


def _orders(count=120, scope="RESEARCH"):
    rows = []
    for index in range(count):
        win = index % 3 != 0
        rows.append(
            {
                "scope": scope,
                "trading_hour": str(index % 24).zfill(2),
                "trading_session": "LONDON" if index % 2 else "NEW_YORK",
                "market_regime": "TREND" if index % 4 else "RANGE",
                "entry_plan": "pullback_continuation",
                "exit_plan": "risk_reward_exit",
                "pattern": "higher_high_higher_low",
                "engine_combination": "structure+liquidity+mtf",
                "profit_reason": "trend_followed" if win else "",
                "loss_reason": "spread_pressure" if not win else "",
                "profit": 4.0 if win else -2.0,
                "drawdown": 1.0 if win else 3.0,
                "risk_score": 1.0 if win else 2.0,
            }
        )
    return rows


def test_research_center_separates_research_statistics_from_live_statistics():
    report = ResearchCenterRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "historical_research_ready": True,
        "research_orders": _orders(120) + _orders(20, scope="LIVE"),
    })

    assert report.status == "READY"
    assert report.research_scope == "RESEARCH_ONLY"
    assert report.live_scope == "LIVE_SEPARATE_NOT_USED_FOR_RESEARCH_RANKING"
    assert report.top_trading_sessions.statistic_scope == "RESEARCH_ONLY"
    assert sum(row.sample_size for row in report.top_trading_sessions.rows) == 120
    assert report.live_execution_enabled is False


def test_research_center_builds_all_required_top_10_dashboard_groups():
    report = ResearchCenterRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "historical_research_ready": True,
        "research_orders": _orders(140),
    })

    groups = [
        report.top_trading_hours,
        report.top_trading_sessions,
        report.top_market_regimes,
        report.top_entry_plans,
        report.top_exit_plans,
        report.top_patterns,
        report.top_engine_combinations,
        report.top_profit_reasons,
        report.top_loss_reasons,
    ]
    assert all(group.rows for group in groups)
    assert all(len(group.rows) <= 10 for group in groups)
    assert all(group.rows[0].rank == 1 for group in groups)


def test_research_center_blocks_non_xm_or_non_gold_version1_policy():
    report = ResearchCenterRuntime().evaluate_one({
        "broker": "EXNESS",
        "symbol": "XAUUSD",
        "historical_research_ready": True,
        "research_orders": _orders(120),
    })

    assert report.status == "BLOCKED"
    assert "version1_xm_only_required" in report.validation_items
    assert "version1_gold_only_required" in report.validation_items
    assert report.trading_logic_changed is False


def test_research_center_waits_for_historical_research_dataset_before_analysis():
    report = ResearchCenterRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "historical_research_ready": False,
        "research_orders": _orders(120),
    })

    assert report.status == "WAITING"
    assert report.reason == "research_center_waiting_for_historical_research_dataset"
    assert "historical_research_dataset_required" in report.validation_items


def test_research_center_standard_learning_requires_100_completed_orders():
    waiting = ResearchCenterRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "historical_research_ready": True,
        "research_orders": _orders(99),
    })
    ready = ResearchCenterRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "historical_research_ready": True,
        "research_orders": _orders(100),
    })

    assert waiting.standard_learning_candidate is False
    assert "minimum_100_research_orders_required" in waiting.validation_items
    assert ready.standard_learning_candidate is True
    assert "temporary_standard_every_100_orders" in ready.standard_learning_policy
    assert "permanent_standard_every_1000_orders" in ready.standard_learning_policy


def test_research_center_rows_include_thai_and_english_explainability():
    report = ResearchCenterRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "historical_research_ready": True,
        "research_orders": _orders(110),
    })
    row = report.top_engine_combinations.rows[0]

    assert row.thai_description
    assert row.english_description
    assert "Research-only" in row.english_description
    assert "วิจัย" in row.thai_description


def test_dashboard_runtime_includes_research_center_dependency():
    report = DashboardRuntimeStatus().evaluate_one({
        "profile_name": "Research",
        "broker": "XM",
        "symbol": "GOLD#",
        "account_type": "DEMO",
        "login": "123456",
        "password": "secret",
        "server": "XMGlobal-MT5 6",
        "mt5_terminal_path": "C:/Program Files/MetaTrader 5/terminal64.exe",
        "initial_capital": 1000,
        "historical_download_requested": True,
        "downloaded_bars": 100000,
        "missing_bars": 0,
        "duplicate_bars": 0,
        "invalid_bars": 0,
        "historical_research_ready": True,
        "research_orders": _orders(120),
        "internet_status": "ONLINE",
        "mt5_status": "CONNECTED",
        "broker_status": "CONNECTED",
        "cpu_usage": 25,
        "ram_usage": 40,
        "disk_usage": 50,
        "heartbeat_age_seconds": 5,
    })

    assert report.research_center_status == "READY"
    assert "research" in report.dashboard_sections
    assert report.live_execution_enabled is False
