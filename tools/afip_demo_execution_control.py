"""Start, stop, and inspect isolated AFIP demo-execution workers."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from typing import Any

from afip.demo_execution_gateway import DemoGatewayConfig
from afip.four_profile_operations.runtime import FourProfileOperationalRuntime, FourProfileSupervisor

CONFIG = Path("config/four_profile_demo.json")


def pid_path(profile: Any) -> Path:
    return profile.runtime_directory / "demo_runner.pid"


def is_running(pid: int) -> bool:
    return FourProfileSupervisor._is_process_running(pid)


def status() -> dict[str, Any]:
    profiles = FourProfileOperationalRuntime(CONFIG).load()
    records = []
    for profile in profiles:
        path = pid_path(profile)
        pid = None
        running = False
        if path.exists():
            try:
                pid = int(path.read_text(encoding="utf-8").strip())
                running = is_running(pid)
            except (OSError, ValueError):
                running = False
            if not running:
                path.unlink(missing_ok=True)
                pid = None
        state_path = profile.runtime_directory / "demo_execution_state.json"
        state = {}
        if state_path.exists():
            try: state = json.loads(state_path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError, TypeError): state = {}
        records.append({
            "profile_id": profile.profile_id,
            "enabled": profile.enabled,
            "runtime_state": "RUNNING" if running else "STOPPED",
            "pid": pid,
            "gateway_status": state.get("status", "NOT_STARTED"),
            "gateway_reason": state.get("reason", "demo gateway has not run"),
            "demo_verified": state.get("demo_verified", False),
            "armed": state.get("armed", False),
            "order_status": state.get("order_status", "ORDER_NOT_SENT"),
            "sent_units": state.get("sent_units", 0),
        })
    return {"status": "READY", "execution": "DEMO_EXECUTION_ONLY", "profiles": records}


def start(selected: list[str] | None) -> dict[str, Any]:
    selected_ids = {x.upper() for x in selected} if selected else None
    for profile in FourProfileOperationalRuntime(CONFIG).load():
        if not profile.enabled or (selected_ids is not None and profile.profile_id not in selected_ids):
            continue
        profile.runtime_directory.mkdir(parents=True, exist_ok=True)
        profile.logs_directory.mkdir(parents=True, exist_ok=True)
        path = pid_path(profile)
        if path.exists():
            try:
                if is_running(int(path.read_text(encoding="utf-8").strip())):
                    continue
            except (OSError, ValueError):
                pass
            path.unlink(missing_ok=True)
        command = [sys.executable, "-c", (
            "from pathlib import Path; from afip.demo_execution_gateway import DemoExecutionRunner, DemoGatewayConfig; "
            f"DemoExecutionRunner(DemoGatewayConfig(profile_id={profile.profile_id!r}, config_path=Path({str(CONFIG)!r}))).run()"
        )]
        log_path = profile.logs_directory / "demo_execution_runner.log"
        with log_path.open("a", encoding="utf-8") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, cwd=str(Path.cwd()))
        path.write_text(str(process.pid), encoding="utf-8")
    return status()


def stop(selected: list[str] | None) -> dict[str, Any]:
    selected_ids = {x.upper() for x in selected} if selected else None
    for profile in FourProfileOperationalRuntime(CONFIG).load():
        if selected_ids is not None and profile.profile_id not in selected_ids:
            continue
        path = pid_path(profile)
        if not path.exists():
            continue
        try:
            pid = int(path.read_text(encoding="utf-8").strip())
            os.kill(pid, signal.SIGTERM)
        except (OSError, ValueError):
            pass
        path.unlink(missing_ok=True)
    return status()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["status", "start-all", "start-selected", "stop-all", "stop-selected", "run-once"])
    parser.add_argument("--profiles", nargs="*")
    args = parser.parse_args()
    if args.command == "status": report = status()
    elif args.command in {"start-all", "start-selected"}: report = start(args.profiles if args.command == "start-selected" else None)
    elif args.command in {"stop-all", "stop-selected"}: report = stop(args.profiles if args.command == "stop-selected" else None)
    else:
        from afip.demo_execution_gateway import DemoExecutionGateway, DemoProfilePolicy
        raw = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
        selected = {x.upper() for x in (args.profiles or ["P1", "P2", "P3", "P4"])}
        operations = FourProfileOperationalRuntime(CONFIG)
        profiles = {x.profile_id: x for x in operations.load()}
        rows = []
        for item in raw["profiles"]:
            pid = str(item["profile_id"]).upper()
            if pid in selected:
                rows.append(DemoExecutionGateway(profiles[pid], DemoProfilePolicy.from_mapping(item)).run_cycle().as_dict())
        report = {"status": "READY", "execution": "DEMO_EXECUTION_ONLY", "profiles": rows}
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__": raise SystemExit(main())
