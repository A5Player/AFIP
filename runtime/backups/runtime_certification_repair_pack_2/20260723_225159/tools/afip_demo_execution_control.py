"""Start, stop and inspect AFIP's single-process sequential MT5 router."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any

from afip.four_profile_operations.runtime import FourProfileOperationalRuntime, FourProfileSupervisor

CONFIG = Path("config/four_profile_demo.json")
ROUTER_PID = Path("runtime/execution/sequential_router.pid")
ROUTER_LOG = Path("runtime/execution/sequential_router.log")
ROUTER_STATE = Path("runtime/execution/sequential_router_status.json")
ISOLATION = Path("runtime/account_isolation_status.json")


def is_running(pid: int) -> bool:
    return FourProfileSupervisor._is_process_running(pid)


def _router_pid() -> int | None:
    if not ROUTER_PID.exists():
        return None
    try:
        pid = int(ROUTER_PID.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        ROUTER_PID.unlink(missing_ok=True)
        return None
    if not is_running(pid):
        ROUTER_PID.unlink(missing_ok=True)
        return None
    return pid


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, TypeError):
        return {}


def _isolation_rows() -> dict[str, dict[str, Any]]:
    payload = _load_json(ISOLATION)
    return {str(x.get("profile_id", "")).upper(): x for x in payload.get("profiles", [])}


def _router_state() -> dict[str, Any]:
    return _load_json(ROUTER_STATE)


def _log_tail(lines: int = 40) -> list[str]:
    try:
        return ROUTER_LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:]
    except OSError:
        return []


def _reset_profile_states(isolation: dict[str, dict[str, Any]]) -> None:
    """Remove misleading ownership data from previous workers before startup."""
    for profile in FourProfileOperationalRuntime(CONFIG).load():
        verified = isolation.get(profile.profile_id, {})
        state_path = profile.runtime_directory / "demo_execution_state.json"
        previous = _load_json(state_path)
        payload = {
            **previous,
            "profile_id": profile.profile_id,
            "status": "RESEARCH_ONLY" if not profile.execution_enabled else "WAITING",
            "reason": "profile_execution_disabled_research_preserved" if not profile.execution_enabled else "sequential_router_starting",
            "order_status": "ORDER_NOT_SENT",
            "sent_units": 0,
            "connected_account_login": verified.get("actual_login", "UNKNOWN"),
            "connected_terminal_folder": verified.get("actual_terminal", "UNKNOWN"),
            "ownership_token": "",
            "binding_verified": verified.get("status") == "PASS",
        }
        state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = state_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        tmp.replace(state_path)


def status() -> dict[str, Any]:
    profiles = FourProfileOperationalRuntime(CONFIG).load()
    router_pid = _router_pid()
    router_state = _router_state()
    isolation = _isolation_rows()
    records = []
    for profile in profiles:
        state_path = profile.runtime_directory / "demo_execution_state.json"
        state = _load_json(state_path)
        verified = isolation.get(profile.profile_id, {})
        actual_login = verified.get("actual_login", "UNKNOWN")
        actual_terminal = verified.get("actual_terminal", "UNKNOWN")
        execution_running = bool(router_pid and profile.enabled and profile.execution_enabled)
        records.append({
            "profile_id": profile.profile_id,
            "enabled": profile.enabled,
            "execution_enabled": profile.execution_enabled,
            "research_enabled": profile.research_enabled,
            "runtime_state": "RUNNING" if execution_running else ("RESEARCH_ONLY" if profile.enabled and profile.research_enabled and not profile.execution_enabled else "STOPPED"),
            "pid": router_pid if execution_running else None,
            "router_mode": "SINGLE_SUPERVISOR_PROCESS_ISOLATED_MT5",
            "gateway_status": state.get("status", "RESEARCH_ONLY" if not profile.execution_enabled else "NOT_STARTED"),
            "gateway_reason": state.get("reason", "execution_disabled_research_preserved" if not profile.execution_enabled else "demo gateway has not run"),
            "demo_verified": state.get("demo_verified", bool(verified.get("status") == "PASS")),
            "armed": state.get("armed", False),
            "order_status": state.get("order_status", "ORDER_NOT_SENT"),
            "sent_units": state.get("sent_units", 0),
            # The authoritative routing identity is the fresh read-only isolation result,
            # never a stale gateway state written by a previous worker.
            "connected_account_login": actual_login,
            "connected_terminal_folder": actual_terminal,
            "last_execution_account_login": state.get("connected_account_login", "NOT_APPLICABLE" if not profile.execution_enabled else "UNKNOWN"),
            "last_execution_terminal_folder": state.get("connected_terminal_folder", "NOT_APPLICABLE" if not profile.execution_enabled else "UNKNOWN"),
            "ownership_token": state.get("ownership_token", ""),
            "binding_verified": verified.get("status") == "PASS",
        })
    return {
        "status": "READY",
        "execution": "DEMO_EXECUTION_ONLY",
        "router": {
            "mode": "SINGLE_SUPERVISOR_PROCESS_ISOLATED_MT5",
            "pid": router_pid,
            "running": router_pid is not None,
            "state": router_state.get("status", "NOT_STARTED"),
            "cycle": router_state.get("cycle", 0),
            "profile_errors": router_state.get("profile_errors", []),
            "concurrent_profile_workers": 0,
        },
        "profiles": records,
    }


def _stop_legacy_workers() -> None:
    for profile in FourProfileOperationalRuntime(CONFIG).load():
        path = profile.runtime_directory / "demo_runner.pid"
        if not path.exists():
            continue
        try:
            os.kill(int(path.read_text(encoding="utf-8").strip()), signal.SIGTERM)
        except (OSError, ValueError):
            pass
        path.unlink(missing_ok=True)


def _wait_for_router(process: subprocess.Popen[Any], timeout_seconds: float = 20.0) -> tuple[bool, str]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        return_code = process.poll()
        if return_code is not None:
            return False, f"router_process_exited:{return_code}"
        pid = _router_pid()
        state = _router_state()
        if pid and state.get("status") in {"BOOTING", "RUNNING"}:
            return True, "router_handshake_complete"
        time.sleep(0.25)
    return False, "router_start_timeout"



def _validate_profile_isolation() -> tuple[bool, str]:
    """Fail closed when enabled profiles share an account or terminal path."""
    try:
        raw = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, TypeError) as exc:
        return False, f"profile_isolation_validation_failed:{type(exc).__name__}"
    seen_accounts: set[tuple[str, str]] = set()
    seen_terminals: set[str] = set()
    for row in raw.get("profiles", []):
        if not row.get("enabled", False) or not row.get("execution_enabled", False):
            continue
        account = (str(row.get("server", "")).casefold(), str(row.get("login_env", "")).casefold())
        terminal = str(row.get("mt5_terminal", "")).replace("/", "\\").rstrip("\\").casefold()
        if account in seen_accounts:
            return False, "profile_isolation_validation_failed:duplicate_account"
        if terminal in seen_terminals:
            return False, "profile_isolation_validation_failed:duplicate_terminal"
        if not terminal:
            return False, "profile_isolation_validation_failed:missing_terminal"
        seen_accounts.add(account); seen_terminals.add(terminal)
    return True, "profile_isolation_validated"

def start(selected: list[str] | None) -> dict[str, Any]:
    from tools.afip_verify_account_isolation import verify

    isolation_ok, isolation_reason = _validate_profile_isolation()
    if not isolation_ok:
        return {"status": "BLOCKED", "reason": isolation_reason, "profiles": status()["profiles"]}

    _stop_legacy_workers()
    report = verify(CONFIG)
    ISOLATION.parent.mkdir(parents=True, exist_ok=True)
    ISOLATION.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not report.get("safe_to_start", False):
        return {
            "status": "BLOCKED",
            "reason": "account_isolation_verification_failed",
            "isolation": report,
            "profiles": status()["profiles"],
        }

    isolation = {str(x.get("profile_id", "")).upper(): x for x in report.get("profiles", [])}
    _reset_profile_states(isolation)

    existing = _router_pid()
    if existing is not None:
        result = status()
        result["start_result"] = "ALREADY_RUNNING"
        return result

    ROUTER_PID.unlink(missing_ok=True)
    ROUTER_STATE.unlink(missing_ok=True)
    ROUTER_LOG.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "tools.afip_profile_sequential_execution_router", "--interval-seconds", "60"]
    if selected:
        command += ["--profiles", *[x.upper() for x in selected]]

    creationflags = 0
    popen_kwargs: dict[str, Any] = {"cwd": str(Path.cwd()), "close_fds": True}
    if os.name == "nt":
        creationflags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        popen_kwargs["creationflags"] = creationflags
    else:
        popen_kwargs["start_new_session"] = True

    with ROUTER_LOG.open("a", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, **popen_kwargs)

    ok, reason = _wait_for_router(process)
    if not ok:
        try:
            process.terminate()
        except OSError:
            pass
        result = status()
        result.update({
            "status": "BLOCKED",
            "reason": reason,
            "router_log_tail": _log_tail(),
        })
        return result

    result = status()
    result["start_result"] = "STARTED"
    return result


def stop(_: list[str] | None = None) -> dict[str, Any]:
    _stop_legacy_workers()
    pid = _router_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        deadline = time.monotonic() + 10
        while _router_pid() and time.monotonic() < deadline:
            time.sleep(0.2)
    ROUTER_PID.unlink(missing_ok=True)
    return status()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["status", "start-all", "start-selected", "stop-all", "stop-selected"])
    parser.add_argument("--profiles", nargs="*")
    args = parser.parse_args()
    if args.command == "status":
        report = status()
    elif args.command.startswith("start"):
        report = start(args.profiles if args.command == "start-selected" else None)
    else:
        report = stop(args.profiles if args.command == "stop-selected" else None)
    print(json.dumps(report, indent=2, default=str))
    return 2 if report.get("status") == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
