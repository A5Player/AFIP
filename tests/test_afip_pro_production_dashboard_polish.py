from __future__ import annotations

from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime


def _profile() -> dict:
    return {
        "profile_id": "P1", "profile_name": "Conservative", "runtime_state": "RUNNING",
        "process_alive": True, "data_fresh": True, "bid": 4041.73, "ask": 4042.05,
        "spread_points": 32.0, "balance": 79.92, "equity": 79.92,
        "free_margin": 79.92, "margin": 0.0, "floating_profit": 0.0,
        "currency": "USD", "financial_live": True, "maximum_units": 3,
        "sent_units": 1, "allocated_units": 1, "tickets": [956151256],
        "runtime_truth": {
            "market_current": "UNKNOWN", "market_current_source": "NO_MARKET_SESSION_EVIDENCE",
            "runtime_current": "RUNNING", "runtime_evidence_fresh": True,
            "mt5_current": "CONNECTED", "mt5_evidence_fresh": True,
            "gateway_current": "WAITING", "gateway_evidence_fresh": True,
            "current_reason": "waiting_for_runtime_evidence",
        },
        "operations_health": {"overall_status": "READY", "operating_mode": "ACTIVE_RUNTIME"},
    }


def test_live_tick_evidence_resolves_unknown_market_without_invention() -> None:
    html = ThreeDashboardRuntime().render_profiles_html({"profiles": [_profile()]})
    assert "OPEN_TICKING" in html
    assert "LIVE_TICK_EVIDENCE" in html


def test_stale_wait_reason_is_normalized_only_when_all_evidence_is_fresh() -> None:
    html = ThreeDashboardRuntime().render_profiles_html({"profiles": [_profile()]})
    assert "waiting_for_next_runtime_cycle" in html
    assert "waiting_for_runtime_evidence" not in html


def test_capacity_and_ticket_semantics_are_explicit() -> None:
    html = ThreeDashboardRuntime().render_profiles_html({"profiles": [_profile()]})
    assert "capacity 3 · allocated 1 · sent 1 · available 2" in html
    assert "current NONE · last 956151256" in html
    assert "NO_OPEN_POSITION" in html
