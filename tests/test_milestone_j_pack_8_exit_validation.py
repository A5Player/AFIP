from datetime import datetime, timezone

from afip.exit_validation import ExitValidationRuntime


def base_record(action="HOLD", units=1):
    return {
        "current_time_utc": datetime(2026, 7, 10, 2, 0, tzinfo=timezone.utc),
        "open_positions": [{
            "position_id": "GOLD-1",
            "symbol": "GOLD#",
            "direction": "BUY",
            "units": units,
            "recommended_action": action,
            "trade_thesis_valid": True,
            "regime_supports_position": True,
            "stop_protected": True,
        }],
        "risk_allowed": True,
        "timing_allowed": True,
        "spread_allowed": True,
    }


def test_hold_context_is_approved_without_execution():
    report = ExitValidationRuntime().evaluate_one(base_record())
    assert report.status == "READY"
    assert report.approved_action == "HOLD"
    assert report.direct_execution is False


def test_partial_close_requires_more_than_one_unit():
    report = ExitValidationRuntime().evaluate_one(base_record("PARTIAL_CLOSE", units=1))
    assert report.status == "WAITING"
    assert report.approved_action == "HOLD"


def test_partial_close_is_available_for_split_units():
    report = ExitValidationRuntime().evaluate_one(base_record("PARTIAL_CLOSE", units=3))
    assert report.status == "READY"
    assert report.approved_action == "PARTIAL_CLOSE"


def test_stop_loss_move_must_reduce_risk():
    record = base_record("MOVE_STOP_LOSS")
    record["open_positions"][0]["new_stop_reduces_risk"] = False
    report = ExitValidationRuntime().evaluate_one(record)
    assert report.status == "WAITING"
    assert "move_stop_loss_requirements_not_met" in report.validations[0].block_reasons


def test_invalid_trade_thesis_can_approve_exit():
    record = base_record("EXIT")
    record["open_positions"][0]["trade_thesis_valid"] = False
    report = ExitValidationRuntime().evaluate_one(record)
    assert report.status == "READY"
    assert report.approved_action == "EXIT"


def test_non_gold_position_is_blocked():
    record = base_record("HOLD")
    record["open_positions"][0]["symbol"] = "EURUSD"
    report = ExitValidationRuntime().evaluate_one(record)
    assert report.status == "WAITING"
    assert "version1_gold_only_required" in report.validations[0].block_reasons
