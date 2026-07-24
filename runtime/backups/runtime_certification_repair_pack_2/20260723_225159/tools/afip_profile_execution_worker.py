"""Persistent, process-isolated AFIP execution worker for exactly one profile.

Each worker owns one profile identity for its entire lifetime. The worker never
changes profile, terminal path, login, server, or magic number. Execution cycles
remain serialized by the gateway routing lock, while MT5 bridge state is isolated
by the operating-system process boundary.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.afip_profile_execution_once import run_once

_stop = False


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _request_stop(*_: object) -> None:
    global _stop
    _stop = True


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def run(profile_id: str, config: Path, interval_seconds: float) -> int:
    profile_id = profile_id.strip().upper()
    runtime_dir = Path("runtime/execution/profile_workers")
    pid_path = runtime_dir / f"{profile_id.lower()}.pid"
    status_path = runtime_dir / f"{profile_id.lower()}.json"

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _request_stop)
        except (ValueError, OSError):
            pass

    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(str(os.getpid()), encoding="utf-8")
    cycle = 0
    _atomic_json(status_path, {
        "schema_version": "afip-profile-execution-worker.v1",
        "profile_id": profile_id,
        "status": "BOOTING",
        "pid": os.getpid(),
        "cycle": cycle,
        "updated_at_utc": _utc_now(),
    })

    try:
        while not _stop:
            started = time.time()
            try:
                report = run_once(profile_id, config)
                worker_status = "RUNNING"
                error = None
            except Exception as exc:
                report = {
                    "profile_id": profile_id,
                    "status": "ERROR",
                    "reason": f"profile_worker_cycle_error:{type(exc).__name__}:{exc}",
                }
                worker_status = "DEGRADED"
                error = report["reason"]
            cycle += 1
            _atomic_json(status_path, {
                "schema_version": "afip-profile-execution-worker.v1",
                "profile_id": profile_id,
                "status": worker_status,
                "pid": os.getpid(),
                "cycle": cycle,
                "last_cycle_started_epoch": started,
                "last_cycle_finished_epoch": time.time(),
                "last_gateway_status": report.get("status"),
                "last_gateway_reason": report.get("reason"),
                "error": error,
                "updated_at_utc": _utc_now(),
            })
            deadline = time.monotonic() + max(5.0, interval_seconds)
            while not _stop and time.monotonic() < deadline:
                time.sleep(0.25)
        return 0
    finally:
        pid_path.unlink(missing_ok=True)
        _atomic_json(status_path, {
            "schema_version": "afip-profile-execution-worker.v1",
            "profile_id": profile_id,
            "status": "STOPPED",
            "pid": None,
            "cycle": cycle,
            "updated_at_utc": _utc_now(),
        })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--config", default="config/four_profile_demo.json")
    parser.add_argument("--interval-seconds", type=float, default=60.0)
    args = parser.parse_args()
    return run(args.profile, Path(args.config), args.interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
