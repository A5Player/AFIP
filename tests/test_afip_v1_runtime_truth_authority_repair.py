from __future__ import annotations

from afip.dashboard_state_machine import normalize_profile_state


def test_fresh_router_authority_overrides_stale_profile_status() -> None:
    result = normalize_profile_state({
        "runtime_state": "RUNNING",
        "mt5_connection": "CONNECTED",
        "source_metadata": {
            "profile_status": {"exists": True, "fresh": False},
            "mt5_health": {"exists": True, "fresh": True},
            "execution_state": {"exists": True, "fresh": True},
            "runtime_authority": {"exists": True, "fresh": True, "router_running": True},
        },
        "gateway_status": "WAITING",
        "demo_gateway_reason": "duplicate_signal_cooldown_active",
    })
    assert result["runtime_current"] == "RUNNING"
    assert result["gateway_current"] == "WAITING"
    assert result["current_reason"] == "duplicate_signal_cooldown_active"


def test_no_live_authority_keeps_stale_runtime_fail_closed() -> None:
    result = normalize_profile_state({
        "runtime_state": "RUNNING",
        "source_metadata": {
            "profile_status": {"exists": True, "fresh": False},
            "runtime_authority": {"exists": True, "fresh": False},
        },
    })
    assert result["runtime_current"] == "STALE"
    assert result["gateway_current"] == "INACTIVE"
    assert result["current_reason"] == "runtime_not_currently_running"
