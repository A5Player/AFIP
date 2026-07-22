from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime


def _profiles():
    return [
        {
            "profile_id": f"P{i}",
            "profile_name": "Profile",
            "runtime_state": "STOPPED",
            "mt5_connection": "CONNECTED",
            "account_balance": 100.0,
            "data_fresh": i != 4,
            "sizing_authority": "LOT_AUTHORITY",
        }
        for i in range(1, 5)
    ]


def test_operations_header_uses_compact_real_dashboard_markup():
    html = ThreeDashboardRuntime().render_profiles_html({"profiles": _profiles()})
    assert '<header class="operations-header">' in html
    assert 'class="operations-summary"' in html
    assert 'class="operations-generated"' in html
    assert 'class="card-label"' in html
    assert 'class="card-progress"' in html


def test_operations_header_css_keeps_title_and_cards_compact():
    html = ThreeDashboardRuntime().render_profiles_html({"profiles": _profiles()})
    assert '.operations-header h1{font-size:20px' in html
    assert '.operations-header .cards{grid-template-columns:repeat(5' in html
    assert '.operations-header .card{padding:8px 10px;min-height:64px}' in html
    assert '.operations-header .card .big{font-size:20px' in html
    assert '.operations-header .card-progress{height:6px}' in html


def test_dashboard_contract_content_is_preserved():
    html = ThreeDashboardRuntime().render_profiles_html({"profiles": _profiles()})
    for text in (
        "AFIP Dashboard 1 · P1–P4",
        "Runtime 0/4 · MT5 4/4",
        "Live financial",
        "Fresh data",
        "Lot policy",
        "DATA_UNAVAILABLE",
    ):
        assert text in html
