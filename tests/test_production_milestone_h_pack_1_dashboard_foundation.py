from afip.dashboard_center import DashboardFoundationRuntime, build_top_rankings, default_engine_catalog, default_intelligence_catalog, status_icon


def _record(**updates):
    data = {
        "market_regime": "TRENDING",
        "signal_context": "SELL_CONTINUATION",
        "execution_mode": "LOCKED_SIMULATION_ONLY",
    }
    data.update(updates)
    return data


def test_dashboard_foundation_blocks_records_without_market_regime():
    profile = DashboardFoundationRuntime().evaluate_one(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"
    assert profile.dashboard_gate == "BLOCKED"


def test_dashboard_foundation_blocks_live_execution_mode():
    profile = DashboardFoundationRuntime().evaluate_one(_record(execution_mode="LIVE"))

    assert profile.status == "BLOCKED"
    assert profile.reason == "live_execution_not_allowed_for_dashboard_foundation"
    assert profile.trading_logic_changed is False


def test_dashboard_foundation_preserves_regime_before_signal_context():
    profile = DashboardFoundationRuntime().evaluate_one(_record(market_regime="sideway", signal_context="buy_reversal"))

    assert profile.market_regime == "SIDEWAY"
    assert profile.signal_context == "BUY_REVERSAL"
    assert profile.status == "READY"


def test_dashboard_foundation_contains_bilingual_intelligence_and_engine_cards():
    profile = DashboardFoundationRuntime().evaluate_one(_record())

    assert profile.status == "READY"
    assert profile.dashboard_gate == "DASHBOARD_FOUNDATION_READY"
    assert profile.bilingual_ready is True
    assert len(profile.intelligence_cards) >= 8
    assert len(profile.engine_cards) >= 5
    assert all(card.name_en and card.name_th and card.function_en and card.function_th for card in profile.intelligence_cards)
    assert all(card.name_en and card.name_th and card.function_en and card.function_th for card in profile.engine_cards)


def test_dashboard_foundation_status_icons_are_deterministic():
    assert status_icon("ready").icon == "🟢"
    assert status_icon("caution").icon == "🟡"
    assert status_icon("disabled").icon == "⚪"
    assert status_icon("failed").icon == "🔴"


def test_dashboard_foundation_top_rankings_and_report_are_stable():
    rankings = build_top_rankings(
        [
            {"label_en": "Hour 20", "label_th": "เวลา 20", "metric_value": 61, "sample_size": 20},
            {"label_en": "Hour 21", "label_th": "เวลา 21", "metric_value": 79, "sample_size": 12},
        ]
    )
    report = DashboardFoundationRuntime().explain_one(_record())

    assert rankings[0].label_en == "Hour 21"
    assert report.as_dict()["trading_logic_changed"] is False
    assert report.as_dict()["total_cards"] >= 13
    assert "Decision reason: dashboard_foundation_ready" in report.as_text()
    assert default_intelligence_catalog()[0].category <= default_intelligence_catalog()[-1].category
    assert default_engine_catalog()[0].category <= default_engine_catalog()[-1].category
