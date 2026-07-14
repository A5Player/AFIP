"""Start, stop and inspect the AFIP live dashboard regeneration service."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

from afip.four_profile_operations.runtime import FourProfileSupervisor

PID_PATH = Path("runtime/dashboard/live_dashboard.pid")
LOG_PATH = Path("runtime/dashboard/live_dashboard.log")
OUTPUT_PATH = Path("runtime/dashboard/afip_dashboard.html")


def _running(pid: int) -> bool:
    return FourProfileSupervisor._is_process_running(pid)


def status() -> dict[str, object]:
    pid = None
    running = False
    if PID_PATH.exists():
        try:
            pid = int(PID_PATH.read_text(encoding="utf-8").strip())
            running = _running(pid)
        except (OSError, ValueError):
            running = False
        if not running:
            PID_PATH.unlink(missing_ok=True)
            pid = None
    return {
        "status": "READY",
        "runtime_state": "RUNNING" if running else "STOPPED",
        "pid": pid,
        "output": str(OUTPUT_PATH),
        "output_exists": OUTPUT_PATH.exists(),
        "refresh_interval_seconds": 5,
    }


def start() -> dict[str, object]:
    current = status()
    if current["runtime_state"] == "RUNNING":
        return current
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-c", "from afip.dashboard_ui.live_service import run_live_dashboard; run_live_dashboard()"]
    with LOG_PATH.open("a", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, cwd=str(Path.cwd()))
    PID_PATH.write_text(str(process.pid), encoding="utf-8")
    return status()


def stop() -> dict[str, object]:
    if PID_PATH.exists():
        try:
            pid = int(PID_PATH.read_text(encoding="utf-8").strip())
            os.kill(pid, signal.SIGTERM)
        except (OSError, ValueError):
            pass
        PID_PATH.unlink(missing_ok=True)
    return status()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start", "status", "stop", "run-once"])
    args = parser.parse_args()
    if args.command == "start": report = start()
    elif args.command == "stop": report = stop()
    elif args.command == "run-once":
        from afip.dashboard_ui.launcher import launch_dashboard
        launch_dashboard(OUTPUT_PATH)
        report = status()
    else: report = status()
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
