from pathlib import Path

from afip.broker.mt5_adapter import MT5Adapter
from afip.dashboard_audit import render as render_audit
from afip.runtime_truth import build_profile_truth
from afip.unified_dashboard import render as render_unified


def test_stale_running_record_is_not_presented_as_running():
    truth = build_profile_truth({
        "profile_id": "P1",
        "enabled": True,
        "process_alive": False,
        "runtime_state": "RUNNING",
        "runtime_truth": {"runtime_current": "STALE", "runtime_evidence_fresh": False},
    })
    assert truth["operational_state"] == "STALE"
    assert truth["runtime_state"] == "STALE"


def test_fresh_runtime_waiting_for_user_started_mt5_is_explicit():
    truth = build_profile_truth({
        "profile_id": "P1",
        "enabled": True,
        "process_alive": False,
        "runtime_truth": {"runtime_current": "RUNNING", "runtime_evidence_fresh": True},
    })
    assert truth["operational_state"] == "WAITING_FOR_MT5"
    assert truth["reason"] == "afip_runtime_running_waiting_for_user_started_mt5"


def test_unified_dashboard_uses_authoritative_runtime_truth():
    html = render_unified({
        "status": "STALE",
        "profiles": [{
            "profile_id": "P1",
            "runtime_state": "RUNNING",
            "authoritative_runtime_truth": {
                "operational_state": "STOPPED",
                "reason": "no_active_afip_runtime",
                "runtime_state": "STOPPED",
                "process_state": "STOPPED",
                "session_state": "DISCONNECTED",
            },
        }],
    })
    assert "no_active_afip_runtime" in html
    assert ">STOPPED<" in html
    assert "Configured MT5 process is not running" not in html


def test_mt5_adapter_reports_disabled_policy_separately_from_missing_package():
    disabled = MT5Adapter(mt5_client=object(), enabled=False).initialize()
    missing = MT5Adapter(mt5_client=None, enabled=True).initialize()
    assert disabled["reason"] == "mt5_adapter_disabled_by_policy"
    assert missing["reason"] == "metatrader5_package_unavailable"


def test_dashboard_audit_contains_provenance_columns():
    html = render_audit({"sources": {"router": {
        "path": "runtime/execution/router.json",
        "current_state": "STALE",
        "exists": True,
        "readable": True,
        "age_seconds": 500,
        "producer": "router",
        "pid": 123,
        "execution_mode": "LOCKED_SIMULATION_ONLY",
    }}})
    assert "Producer" in html
    assert "PID" in html
    assert "Execution Mode" in html
    assert "STALE" in html
