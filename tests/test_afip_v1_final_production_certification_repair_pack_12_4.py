from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime, _profile_rows


def _rows(profile):
    return {label: value for _, label, value in _profile_rows(profile)}


def test_stopped_runtime_uses_inactive_position_semantics():
    rows = _rows({
        "runtime_state": "STOPPED",
        "positions_total": 0,
        "data_fresh": False,
        "runtime_truth": {"runtime_current": "STOPPED"},
        "operations_health": {},
    })
    assert rows["SL / TP"] == "NO_ACTIVE_POSITION"


def test_active_or_unspecified_runtime_uses_open_position_semantics():
    rows = _rows({
        "positions_total": 0,
        "data_fresh": True,
        "runtime_truth": {},
        "operations_health": {},
    })
    assert rows["SL / TP"] == "NO_OPEN_POSITION"


def test_rendered_active_dashboard_preserves_production_polish_contract():
    html = ThreeDashboardRuntime().render_profiles_html({
        "profiles": [{
            "profile_id": "P1",
            "runtime_state": "RUNNING",
            "positions_total": 0,
            "data_fresh": True,
            "runtime_truth": {"runtime_current": "RUNNING"},
            "operations_health": {},
        }]
    })
    assert "NO_OPEN_POSITION" in html
