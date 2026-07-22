"""AFIP supervisor for sequential, process-isolated MT5 profile execution.

The supervisor never imports or initializes MetaTrader5. For every profile it
starts one short-lived child Python process, waits for it to finish, and only
then starts the next profile. Therefore:

* no profile workers overlap;
* each child owns exactly one MT5 terminal;
* MetaTrader5 process-global session state cannot leak from P1 to P2/P3/P4;
* a native MT5 crash can terminate only the child, not the router supervisor.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from afip.four_profile_operations.runtime import FourProfileOperationalRuntime
from afip.production_runtime_authority import clean_stale_runtime, RUNTIME_AUTHORITY_VERSION

CONFIG = Path("config/four_profile_demo.json")
ROUTER_PID = Path("runtime/execution/sequential_router.pid")
ROUTER_STATE = Path("runtime/execution/sequential_router_status.json")
PROFILE_LOG_DIR = Path("runtime/execution/profile_cycles")

_stop = False
_active_child: subprocess.Popen[Any] | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _request_stop(*_: object) -> None:
    global _stop
    _stop = True
    child = _active_child
    if child is not None and child.poll() is None:
        try:
            child.terminate()
        except OSError:
            pass


def _write(payload: dict[str, Any]) -> None:
    ROUTER_STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = ROUTER_STATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    tmp.replace(ROUTER_STATE)


def _base_state(status: str, cycles: int) -> dict[str, Any]:
    return {
        "schema_version": "afip-sequential-profile-router.v3",
        "status": status,
        "pid": os.getpid(),
        "cycle": cycles,
        "mode": "SINGLE_SUPERVISOR_PROCESS_ISOLATED_MT5",
        "concurrent_profile_workers": 0,
        "active_profile_worker": None,
        "updated_at_utc": _utc_now(),
        "updated_at_epoch": time.time(),
        "runtime_authority": RUNTIME_AUTHORITY_VERSION,
    }


def _run_profile(profile_id: str) -> tuple[dict[str, Any], dict[str, str] | None]:
    global _active_child
    PROFILE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = PROFILE_LOG_DIR / f"{profile_id.lower()}.log"
    command = [
        sys.executable,
        "-m",
        "tools.afip_profile_execution_once",
        "--profile",
        profile_id,
        "--config",
        str(CONFIG),
    ]
    with log_path.open("a", encoding="utf-8") as log:
        _active_child = subprocess.Popen(
            command,
            cwd=str(Path.cwd()),
            stdout=log,
            stderr=subprocess.STDOUT,
            close_fds=True,
        )
        child_pid = _active_child.pid
        return_code = _active_child.wait()
        _active_child = None

    row = {
        "profile_id": profile_id,
        "worker_pid": child_pid,
        "return_code": return_code,
        "log": str(log_path),
    }
    if return_code != 0:
        return row, {
            "profile_id": profile_id,
            "error_type": "ProfileWorkerExit",
            "error": f"profile_worker_exited:{return_code}",
            "log": str(log_path),
        }
    return row, None


def run(interval_seconds: float, selected: set[str] | None = None) -> int:
    global _stop
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _request_stop)
        except (ValueError, OSError):
            pass

    clean_stale_runtime(Path.cwd())
    ROUTER_PID.parent.mkdir(parents=True, exist_ok=True)
    ROUTER_PID.write_text(str(os.getpid()), encoding="utf-8")
    cycles = 0
    _write({**_base_state("BOOTING", cycles), "profiles_processed": [], "profile_errors": []})

    try:
        while not _stop:
            profiles = FourProfileOperationalRuntime(CONFIG).load()
            rows: list[dict[str, Any]] = []
            errors: list[dict[str, str]] = []

            for profile in profiles:
                profile_id = profile.profile_id.upper()
                if _stop:
                    break
                if selected and profile_id not in selected:
                    continue
                if not profile.enabled or not profile.execution_enabled:
                    continue

                _write({
                    **_base_state("RUNNING", cycles),
                    "active_profile_worker": profile_id,
                    "profiles_processed": [row["profile_id"] for row in rows],
                    "profile_errors": errors,
                })
                try:
                    row, error = _run_profile(profile_id)
                except Exception as exc:
                    row = {
                        "profile_id": profile_id,
                        "worker_pid": None,
                        "return_code": None,
                        "log": str(PROFILE_LOG_DIR / f"{profile_id.lower()}.log"),
                    }
                    error = {
                        "profile_id": profile_id,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "log": row["log"],
                    }
                rows.append(row)
                if error is not None:
                    errors.append(error)
                # Extra release interval before a different terminal process starts.
                time.sleep(1.0)

            cycles += 1
            _write({
                **_base_state("RUNNING", cycles),
                "profiles_processed": [row["profile_id"] for row in rows],
                "profile_workers": rows,
                "profile_errors": errors,
            })

            deadline = time.monotonic() + interval_seconds
            while not _stop and time.monotonic() < deadline:
                time.sleep(0.25)
        return 0
    finally:
        ROUTER_PID.unlink(missing_ok=True)
        _write({
            **_base_state("STOPPED", cycles),
            "pid": None,
            "profiles_processed": [],
            "profile_errors": [],
        })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval-seconds", type=float, default=60.0)
    parser.add_argument("--profiles", nargs="*")
    args = parser.parse_args()
    selected = {x.upper() for x in args.profiles} if args.profiles else None
    return run(max(5.0, args.interval_seconds), selected)


if __name__ == "__main__":
    raise SystemExit(main())
