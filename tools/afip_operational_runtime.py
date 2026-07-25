"""AFIP V1 single-command operational runtime control."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from afip.operational_runtime import OperationalRuntime, read_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("start", "stop", "restart", "status", "once", "worker"))
    parser.add_argument("--interval-seconds", type=int, default=60)
    args = parser.parse_args()
    runtime = OperationalRuntime(Path.cwd(), interval_seconds=args.interval_seconds)
    if args.command == "worker":
        return runtime.run_forever()
    if args.command == "start":
        # The operational supervisor owns the router lifecycle. This command never
        # starts a second runtime path and never launches MetaTrader 5.
        operational = runtime.start_background()
        payload = {
            "status": operational.get("status"),
            "operational_runtime": operational,
            "lifecycle_authority": "OPERATIONAL_SUPERVISOR",
            "execution_authority_bypassed": False,
            "mt5_auto_launch": False,
        }
        print(json.dumps(payload, indent=2, default=str))
        return 0 if operational.get("status") in {"STARTED", "ALREADY_RUNNING"} else 2
    if args.command == "stop":
        operational = runtime.stop()
        print(json.dumps({"status": "STOPPED", "operational_runtime": operational, "lifecycle_authority": "OPERATIONAL_SUPERVISOR"}, indent=2, default=str))
        return 0
    if args.command == "restart":
        stopped = runtime.stop()
        started = runtime.start_background()
        payload = {
            "status": started.get("status"),
            "stop_result": stopped,
            "start_result": started,
            "lifecycle_authority": "OPERATIONAL_SUPERVISOR",
            "mt5_auto_launch": False,
        }
        print(json.dumps(payload, indent=2, default=str))
        return 0 if started.get("status") in {"STARTED", "ALREADY_RUNNING"} else 2
    if args.command == "once":
        print(json.dumps(runtime.run_once(), indent=2, default=str))
        return 0
    payload = read_json(runtime.authority_path)
    payload["supervisor_pid"] = runtime.pid()
    payload["supervisor_running"] = runtime.pid() is not None
    print(json.dumps(payload or {"status": "NOT_STARTED", "supervisor_running": False}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
