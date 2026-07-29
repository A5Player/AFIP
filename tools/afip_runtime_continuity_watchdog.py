"""AFIP runtime continuity watchdog.

Restores the existing research, dashboard, and sequential-router processes only
while START_AFIP has explicitly set the desired runtime state to RUNNING.
It has no MT5 launch, login, reconnect, order-check, or order-send authority.
"""
from __future__ import annotations

import argparse
import os
import signal
import time
from pathlib import Path

from afip.final_integration.io import atomic_json, utc_now
from afip.final_integration.runtime import FinalIntegrationRuntime

_STOP = False


def _request_stop(*_: object) -> None:
    global _STOP
    _STOP = True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--interval", type=int, default=10)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    runtime = FinalIntegrationRuntime(root)
    interval = max(5, int(args.interval))

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _request_stop)
        except Exception:
            pass

    cycles = 0
    recoveries = 0
    while not _STOP and not runtime.watchdog_stop_flag.exists():
        if runtime._desired_state() != "RUNNING":
            break
        result = runtime.ensure_services(include_watchdog=False)
        actions = list(result.get("actions", []))
        recoveries += len([item for item in actions if item.endswith("_started")])
        cycles += 1
        atomic_json(
            runtime.watchdog_status_path,
            {
                "schema_version": "afip-runtime-continuity-watchdog.v1",
                "status": "RUNNING",
                "reason": "runtime_services_supervised",
                "updated_at_utc": utc_now(),
                "heartbeat_utc": utc_now(),
                "pid": os.getpid(),
                "cycles": cycles,
                "recoveries": recoveries,
                "last_actions": actions,
                "interval_seconds": interval,
                "desired_state": "RUNNING",
                "execution_authority": False,
                "order_send_called": False,
                "mt5_auto_launch_allowed": False,
            },
        )
        for _ in range(interval):
            if _STOP or runtime.watchdog_stop_flag.exists():
                break
            time.sleep(1)

    atomic_json(
        runtime.watchdog_status_path,
        {
            "schema_version": "afip-runtime-continuity-watchdog.v1",
            "status": "STOPPED",
            "reason": "stop_requested_or_desired_state_stopped",
            "updated_at_utc": utc_now(),
            "pid": None,
            "cycles": cycles,
            "recoveries": recoveries,
            "execution_authority": False,
            "order_send_called": False,
            "mt5_auto_launch_allowed": False,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
