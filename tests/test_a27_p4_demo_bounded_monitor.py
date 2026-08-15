from pathlib import Path

from tools.afip_a27_p4_demo_bounded_monitor import monitor


def _proof(reason="current_pattern_not_research_eligible", *, sent=0, checks=0, sends=0):
    return {
        "status": ("BROKER_OPEN_ACKNOWLEDGED_MANUAL_CLOSE_REQUIRED" if sent else
                   "NO_ORDER_SENT_GATES_OR_GUARD_BLOCKED"),
        "gateway_status": "ORDER_SENT" if sent else "WAITING",
        "gateway_reason": reason,
        "order_check_calls": checks,
        "order_send_calls": sends,
        "sent_units": sent,
        "tickets": [123] if sent else [],
        "gateway_report": {"decision_action": "BUY", "decision_confidence": 99,
                           "research_eligible": sent == 1},
    }


def test_monitor_stops_immediately_after_one_acknowledged_order(tmp_path: Path):
    values = iter([_proof(), _proof("protected_demo_orders_sent", sent=1, checks=1, sends=1)])
    sleeps = []
    result = monitor(tmp_path, approved=True, attempt_runner=lambda *args: next(values),
                     monotonic=lambda: 0, sleeper=sleeps.append,
                     interval_seconds=1, maximum_duration_seconds=10, maximum_attempts=5)
    assert result["status"] == "BROKER_OPEN_ACKNOWLEDGED_MANUAL_CLOSE_REQUIRED"
    assert result["attempt_count"] == 2 and result["total_sent_units"] == 1
    assert result["total_order_send_calls"] == 1 and sleeps == [1.0]


def test_monitor_stops_on_unconfirmed_broker_attempt(tmp_path: Path):
    result = monitor(tmp_path, approved=True,
                     attempt_runner=lambda *args: _proof("broker_rejected", checks=1),
                     monotonic=lambda: 0, sleeper=lambda value: None)
    assert result["status"] == "BROKER_ATTEMPT_WITHOUT_CONFIRMED_SINGLE_OPEN_STOPPED"
    assert result["attempt_count"] == 1


def test_monitor_never_exceeds_configured_attempt_bound(tmp_path: Path):
    result = monitor(tmp_path, approved=True, attempt_runner=lambda *args: _proof(),
                     monotonic=lambda: 0, sleeper=lambda value: None,
                     interval_seconds=1, maximum_duration_seconds=10, maximum_attempts=3)
    assert result["status"] == "BOUNDED_MONITOR_EXPIRED_NO_ORDER"
    assert result["attempt_count"] == 3 and result["total_order_send_calls"] == 0


def test_existing_position_or_cooldown_requires_operator_review(tmp_path: Path):
    result = monitor(tmp_path, approved=True,
                     attempt_runner=lambda *args: _proof("duplicate_signal_cooldown_active"),
                     monotonic=lambda: 0, sleeper=lambda value: None)
    assert result["status"] == "POSITION_OR_AUTHORITY_STATE_REQUIRES_OPERATOR_REVIEW"
    assert result["attempt_count"] == 1


def test_attempt_exception_stops_without_retry(tmp_path: Path):
    calls = []
    def failed(*args):
        calls.append(1)
        raise RuntimeError("connection_lost")
    result = monitor(tmp_path, approved=True, attempt_runner=failed,
                     monotonic=lambda: 0, sleeper=lambda value: None)
    assert result["status"] == "MONITOR_ATTEMPT_EXCEPTION_STOPPED"
    assert result["attempt_count"] == 0 and len(calls) == 1
