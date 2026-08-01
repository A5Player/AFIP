from pathlib import Path

from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime, _profile_rows


def _row_map(profile):
    return {label: value for _, label, value in _profile_rows(profile)}


def test_no_position_uses_production_dashboard_contract():
    rows = _row_map({
        "positions_total": 0,
        "data_fresh": True,
        "runtime_truth": {},
        "operations_health": {},
    })
    assert rows["SL / TP"] == "NO_OPEN_POSITION"


def test_rendered_dashboard_contains_explicit_no_open_position_semantics():
    html = ThreeDashboardRuntime().render_profiles_html({
        "profiles": [{
            "profile_id": "P1",
            "positions_total": 0,
            "data_fresh": True,
            "runtime_truth": {},
            "operations_health": {},
            "maximum_units": 3,
            "allocated_units": 1,
            "sent_units": 1,
            "tickets": [956151256],
        }]
    })
    assert "NO_OPEN_POSITION" in html


def test_pack_changes_only_dashboard_semantics_source():
    source = Path("afip/dashboard_ui/split_runtime.py").read_text(encoding="utf-8")
    # Pack 12.4 introduced context-aware no-position semantics:
    # inactive runtime => NO_ACTIVE_POSITION
    # active/waiting runtime => NO_OPEN_POSITION
    assert "NO_OPEN_POSITION" in source
    assert "NO_ACTIVE_POSITION" in source

