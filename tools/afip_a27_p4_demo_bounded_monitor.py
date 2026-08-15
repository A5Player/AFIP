"""Bounded P4 Demo monitor using the existing A27 open-only proof authority."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any, Callable, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.afip_a27_p4_demo_open_only_proof import run as run_open_proof

INTERVAL_SECONDS = 300
MAXIMUM_DURATION_SECONDS = 4 * 60 * 60
MAXIMUM_ATTEMPTS = 49

_POSITION_OR_AUTHORITY_STOP_TOKENS = (
    "position", "manual", "capacity", "cooldown", "ownership", "binding",
    "routing_lock", "account", "demo", "symbol", "ambiguous", "partial",
)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _summary(value: Mapping[str, Any], attempt_number: int) -> dict[str, Any]:
    gateway = value.get("gateway_report", {})
    if not isinstance(gateway, Mapping):
        gateway = {}
    return {
        "attempt": attempt_number,
        "observed_at_utc": str(gateway.get("checked_at_utc") or _utc()),
        "proof_status": str(value.get("status", "UNKNOWN")),
        "gateway_status": str(value.get("gateway_status", "UNKNOWN")),
        "gateway_reason": str(value.get("gateway_reason", "unknown")),
        "decision_action": str(gateway.get("decision_action", "WAIT")),
        "decision_confidence": float(gateway.get("decision_confidence", 0.0) or 0.0),
        "research_eligible": bool(gateway.get("research_eligible", False)),
        "trading_cost_status": str(gateway.get("trading_cost_status", "UNKNOWN")),
        "spread_points": float(gateway.get("spread_points", 0.0) or 0.0),
        "order_check_calls": int(value.get("order_check_calls", 0) or 0),
        "order_send_calls": int(value.get("order_send_calls", 0) or 0),
        "sent_units": int(value.get("sent_units", 0) or 0),
        "tickets": list(value.get("tickets", ()) or ()),
    }


def _stop_reason(item: Mapping[str, Any]) -> str | None:
    if item["proof_status"] == "BROKER_OPEN_ACKNOWLEDGED_MANUAL_CLOSE_REQUIRED":
        return "BROKER_OPEN_ACKNOWLEDGED_MANUAL_CLOSE_REQUIRED"
    if item["order_check_calls"] or item["order_send_calls"]:
        return "BROKER_ATTEMPT_WITHOUT_CONFIRMED_SINGLE_OPEN_STOPPED"
    status = str(item["gateway_status"]).upper()
    reason = str(item["gateway_reason"]).lower()
    if status in {"ERROR", "BLOCKED", "STOPPED"}:
        return f"GATEWAY_{status}_STOPPED"
    if any(token in reason for token in _POSITION_OR_AUTHORITY_STOP_TOKENS):
        return "POSITION_OR_AUTHORITY_STATE_REQUIRES_OPERATOR_REVIEW"
    return None


def monitor(
    project_root: Path,
    *,
    approved: bool,
    attempt_runner: Callable[[Path, bool, bool], Mapping[str, Any]] = run_open_proof,
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
    interval_seconds: int = INTERVAL_SECONDS,
    maximum_duration_seconds: int = MAXIMUM_DURATION_SECONDS,
    maximum_attempts: int = MAXIMUM_ATTEMPTS,
    progress: Callable[[Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    if not approved:
        raise ValueError("explicit A27 bounded-monitor approval is required")
    if interval_seconds <= 0 or maximum_duration_seconds <= 0 or maximum_attempts <= 0:
        raise ValueError("bounded-monitor limits must be positive")
    started = monotonic()
    attempts: list[dict[str, Any]] = []
    final_proof: dict[str, Any] = {}
    final_status = "BOUNDED_MONITOR_EXPIRED_NO_ORDER"
    final_reason = "four_hour_limit_reached_without_eligible_signal"

    for number in range(1, maximum_attempts + 1):
        elapsed = monotonic() - started
        if elapsed > maximum_duration_seconds:
            break
        try:
            value = dict(attempt_runner(project_root.resolve(), True, True))
        except Exception as exc:
            final_status = "MONITOR_ATTEMPT_EXCEPTION_STOPPED"
            final_reason = f"{type(exc).__name__}:{exc}"
            break
        item = _summary(value, number)
        attempts.append(item)
        final_proof = value
        if progress is not None:
            progress(item)
        stop = _stop_reason(item)
        if stop is not None:
            final_status = stop
            final_reason = str(item["gateway_reason"])
            break
        remaining = maximum_duration_seconds - (monotonic() - started)
        if number >= maximum_attempts or remaining < interval_seconds:
            break
        sleeper(float(interval_seconds))

    sent = sum(int(item["sent_units"]) for item in attempts)
    check_calls = sum(int(item["order_check_calls"]) for item in attempts)
    send_calls = sum(int(item["order_send_calls"]) for item in attempts)
    if sent > 1 or send_calls > 1 or check_calls > 1:
        final_status = "SAFETY_INVARIANT_VIOLATION_STOPPED"
        final_reason = "more_than_one_broker_attempt_observed"
    return {
        "schema": "afip.a27.p4_demo_bounded_monitor.v1",
        "status": final_status,
        "reason": final_reason,
        "profile_id": "P4",
        "symbol": "GOLD#",
        "authorized_lot": 0.01,
        "maximum_authorized_orders": 1,
        "interval_seconds": interval_seconds,
        "maximum_duration_seconds": maximum_duration_seconds,
        "attempt_count": len(attempts),
        "total_order_check_calls": check_calls,
        "total_order_send_calls": send_calls,
        "total_sent_units": sent,
        "automatic_close_performed": False,
        "manual_close_required": final_status == "BROKER_OPEN_ACKNOWLEDGED_MANUAL_CLOSE_REQUIRED",
        "attempts": attempts,
        "final_gateway_proof": final_proof,
    }


def main(argv: Iterable[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--approve-p4-demo-bounded-monitor", action="store_true")
    args = parser.parse_args(argv)

    def show(item: Mapping[str, Any]) -> None:
        print(
            f"A27 attempt {item['attempt']}: {item['gateway_status']} / "
            f"{item['gateway_reason']} / confidence={item['decision_confidence']} / "
            f"research_eligible={item['research_eligible']} / sent={item['sent_units']}",
            flush=True,
        )

    try:
        result = monitor(
            Path(args.project_root), approved=args.approve_p4_demo_bounded_monitor,
            progress=show,
        )
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    encoded = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
