"""Safe continuous runner for AFIP locked simulation acceptance.

This module is an operational entry point only. It never authorizes direct or live
execution and never calls a broker order API.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import signal
import time
from typing import Any, Callable


LOCKED_EXECUTION = "LOCKED_SIMULATION_ONLY"
NO_ORDER_SENT = "NO_ORDER_SENT"


@dataclass(frozen=True)
class LockedSimulationConfig:
    interval_seconds: float = 60.0
    maximum_cycles: int | None = None
    runtime_directory: Path = Path("runtime/locked_simulation")
    refresh_dashboard: bool = True

    def validate(self) -> None:
        if self.interval_seconds < 1.0:
            raise ValueError("interval_seconds_must_be_at_least_one")
        if self.maximum_cycles is not None and self.maximum_cycles < 1:
            raise ValueError("maximum_cycles_must_be_positive")


@dataclass(frozen=True)
class LockedSimulationSummary:
    started_at_utc: str
    stopped_at_utc: str
    completed_cycles: int
    recorded_snapshots: int
    duplicate_snapshots: int
    failed_cycles: int
    execution: str = LOCKED_EXECUTION
    order_status: str = NO_ORDER_SENT
    live_execution: bool = False
    direct_execution: bool = False


class LockedSimulationRunner:
    """Runs AFIP simulation cycles continuously with immutable execution locks."""

    def __init__(
        self,
        config: LockedSimulationConfig | None = None,
        *,
        simulate: Callable[[], dict[str, Any]] | None = None,
        dashboard_builder: Callable[[], Any] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.config = config or LockedSimulationConfig()
        self.config.validate()
        self._simulate = simulate or self._default_simulate
        self._dashboard_builder = dashboard_builder or self._default_dashboard_builder
        self._sleep = sleep
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._stop_requested = False
        self._last_fingerprint: str | None = None

    @staticmethod
    def _default_simulate() -> dict[str, Any]:
        from afip.runtime.runtime_v1 import RuntimeV1

        return RuntimeV1().simulate()

    @staticmethod
    def _default_dashboard_builder() -> Any:
        from afip.dashboard_ui.launcher import launch_dashboard

        return launch_dashboard()

    def request_stop(self, *_: Any) -> None:
        self._stop_requested = True

    def _utc(self) -> str:
        return self._clock().astimezone(timezone.utc).isoformat()

    def _paths(self) -> dict[str, Path]:
        root = self.config.runtime_directory
        return {
            "root": root,
            "events": root / "events.jsonl",
            "status": root / "status.json",
            "summary": root / "acceptance_summary.json",
        }

    @staticmethod
    def _safe_snapshot(result: dict[str, Any], observed_at_utc: str) -> dict[str, Any]:
        decision = result.get("decision", {})
        order = result.get("order", {})
        confluence = result.get("multi_timeframe_confluence", {})
        risk = result.get("risk", {})
        trading_cost = result.get("trading_cost_intelligence", {})
        return {
            "observed_at_utc": observed_at_utc,
            "status": result.get("status"),
            "mode": result.get("mode"),
            "symbol": result.get("symbol"),
            "data_status": result.get("data_status"),
            "data_source": result.get("data_source"),
            "primary_timeframe": result.get("primary_timeframe"),
            "multi_timeframe_direction": confluence.get("direction"),
            "multi_timeframe_confidence": confluence.get("confidence"),
            "decision_action": decision.get("action"),
            "decision_confidence": decision.get("confidence"),
            "decision_reason": decision.get("reason"),
            "spread_points": trading_cost.get("spread_points"),
            "trading_cost_status": trading_cost.get("status"),
            "risk_allowed": risk.get("allowed", False),
            "risk_reasons": tuple(risk.get("reasons", [])),
            "simulation_order_status": order.get("status"),
            "simulation_action": order.get("action"),
            "simulation_lot": order.get("lot"),
            "execution": LOCKED_EXECUTION,
            "order_status": NO_ORDER_SENT,
            "live_execution": False,
            "direct_execution": False,
        }

    @staticmethod
    def _fingerprint(snapshot: dict[str, Any]) -> str:
        stable = {key: value for key, value in snapshot.items() if key != "observed_at_utc"}
        payload = json.dumps(stable, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
        temporary.replace(path)

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, sort_keys=True, default=str) + "\n")

    def _install_signal_handlers(self) -> dict[int, Any]:
        previous: dict[int, Any] = {}
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                previous[sig] = signal.getsignal(sig)
                signal.signal(sig, self.request_stop)
            except (ValueError, OSError):
                pass
        return previous

    @staticmethod
    def _restore_signal_handlers(previous: dict[int, Any]) -> None:
        for sig, handler in previous.items():
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):
                pass

    def run(self) -> LockedSimulationSummary:
        paths = self._paths()
        paths["root"].mkdir(parents=True, exist_ok=True)
        started = self._utc()
        completed = recorded = duplicates = failures = 0
        previous_handlers = self._install_signal_handlers()

        try:
            while not self._stop_requested:
                cycle_started = self._utc()
                try:
                    result = self._simulate()
                    snapshot = self._safe_snapshot(result, cycle_started)
                    fingerprint = self._fingerprint(snapshot)
                    duplicate = fingerprint == self._last_fingerprint
                    completed += 1
                    if duplicate:
                        duplicates += 1
                    else:
                        snapshot["fingerprint"] = fingerprint
                        self._append_jsonl(paths["events"], snapshot)
                        self._last_fingerprint = fingerprint
                        recorded += 1

                    if self.config.refresh_dashboard:
                        self._dashboard_builder()

                    status = {
                        "runtime_state": "RUNNING",
                        "started_at_utc": started,
                        "last_cycle_utc": cycle_started,
                        "completed_cycles": completed,
                        "recorded_snapshots": recorded,
                        "duplicate_snapshots": duplicates,
                        "failed_cycles": failures,
                        "last_snapshot_duplicate": duplicate,
                        "last_fingerprint": fingerprint,
                        "execution": LOCKED_EXECUTION,
                        "order_status": NO_ORDER_SENT,
                        "live_execution": False,
                        "direct_execution": False,
                    }
                    self._write_json(paths["status"], status)
                    print(
                        f"[{cycle_started}] cycle={completed} "
                        f"action={snapshot.get('decision_action')} "
                        f"confidence={snapshot.get('decision_confidence')} "
                        f"duplicate={duplicate} execution={LOCKED_EXECUTION} {NO_ORDER_SENT}",
                        flush=True,
                    )
                except Exception as exc:  # operational boundary; failure is recorded and runner continues
                    failures += 1
                    completed += 1
                    error = {
                        "observed_at_utc": cycle_started,
                        "event": "cycle_failure",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "execution": LOCKED_EXECUTION,
                        "order_status": NO_ORDER_SENT,
                    }
                    self._append_jsonl(paths["events"], error)
                    self._write_json(
                        paths["status"],
                        {
                            "runtime_state": "DEGRADED",
                            "started_at_utc": started,
                            "last_cycle_utc": cycle_started,
                            "completed_cycles": completed,
                            "recorded_snapshots": recorded,
                            "duplicate_snapshots": duplicates,
                            "failed_cycles": failures,
                            "last_error": error,
                            "execution": LOCKED_EXECUTION,
                            "order_status": NO_ORDER_SENT,
                            "live_execution": False,
                            "direct_execution": False,
                        },
                    )
                    print(f"[{cycle_started}] cycle failure: {type(exc).__name__}: {exc}", flush=True)

                if self.config.maximum_cycles is not None and completed >= self.config.maximum_cycles:
                    break
                if not self._stop_requested:
                    self._sleep(self.config.interval_seconds)
        finally:
            self._restore_signal_handlers(previous_handlers)

        summary = LockedSimulationSummary(
            started_at_utc=started,
            stopped_at_utc=self._utc(),
            completed_cycles=completed,
            recorded_snapshots=recorded,
            duplicate_snapshots=duplicates,
            failed_cycles=failures,
        )
        self._write_json(paths["summary"], asdict(summary))
        self._write_json(paths["status"], {"runtime_state": "STOPPED", **asdict(summary)})
        return summary
