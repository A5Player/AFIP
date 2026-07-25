"""AFIP V1 operational acceptance runtime.

Coordinates existing demo execution, research collection and dashboard generation
without introducing a second execution path.  The sequential router remains the
only order authority.  This module owns observability only.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any, Mapping

SCHEMA_VERSION = "afip-v1-operational-runtime.v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}


def atomic_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    temporary.replace(path)
    return path


def process_alive(pid: int | None) -> bool:
    """Check whether a process exists without signalling it on Windows."""
    if not pid or pid <= 0:
        return False

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        ERROR_ACCESS_DENIED = 5

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        kernel32.OpenProcess.argtypes = [
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        ]
        kernel32.OpenProcess.restype = wintypes.HANDLE

        kernel32.GetExitCodeProcess.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL

        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        handle = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            pid,
        )

        if not handle:
            return ctypes.get_last_error() == ERROR_ACCESS_DENIED

        try:
            exit_code = wintypes.DWORD()

            if not kernel32.GetExitCodeProcess(
                handle,
                ctypes.byref(exit_code),
            ):
                return False

            return exit_code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)

    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False

    return True

def file_age_seconds(path: Path) -> float | None:
    try:
        return max(0.0, time.time() - path.stat().st_mtime)
    except OSError:
        return None


class OperationalRuntime:
    def __init__(self, project_root: str | Path = ".", *, interval_seconds: int = 60) -> None:
        self.root = Path(project_root).resolve()
        self.interval = max(15, int(interval_seconds))
        self.directory = self.root / "runtime" / "operational"
        self.authority_path = self.directory / "authority.json"
        self.pid_path = self.directory / "supervisor.pid"
        self.lock_path = self.directory / "supervisor.lock"
        self.log_path = self.directory / "supervisor.log"
        self.stop_requested = False


    def _acquire_supervisor_lock(self) -> bool:
        """Atomically claim the one allowed operational supervisor."""
        self.directory.mkdir(parents=True, exist_ok=True)
        for attempt in range(2):
            try:
                descriptor = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                owner = read_json(self.lock_path)
                try:
                    owner_pid = int(owner.get("pid"))
                except (TypeError, ValueError):
                    owner_pid = None
                if process_alive(owner_pid):
                    return False
                if attempt == 0:
                    self.lock_path.unlink(missing_ok=True)
                    continue
                return False
            else:
                payload = json.dumps({"pid": os.getpid(), "created_at_utc": utc_now()})
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    handle.write(payload)
                return True
        return False

    def _release_supervisor_lock(self) -> None:
        owner = read_json(self.lock_path)
        try:
            owner_pid = int(owner.get("pid"))
        except (TypeError, ValueError):
            owner_pid = None
        if owner_pid in (None, os.getpid()):
            self.lock_path.unlink(missing_ok=True)

    def _start_execution_router(self) -> dict[str, Any]:
        from tools.afip_demo_execution_control import start
        return start(None)

    def _stop_execution_router(self) -> dict[str, Any]:
        from tools.afip_demo_execution_control import stop
        return stop(None)

    def _router_status(self) -> dict[str, Any]:
        from tools.afip_demo_execution_control import status
        return status()

    def _collect_research(self) -> dict[str, Any]:
        from afip.four_profile_operations.runtime import FourProfileOperationalRuntime
        from afip.research_data_foundation import ResearchRuntimeCollector
        profiles = FourProfileOperationalRuntime(self.root / "config" / "four_profile_demo.json").load()
        ledgers = [p.logs_directory / "demo_execution_ledger.jsonl" for p in profiles if p.enabled and p.research_enabled]
        # Profile paths in configuration are relative to the project root.
        ledgers = [path if path.is_absolute() else self.root / path for path in ledgers]
        return ResearchRuntimeCollector(self.root / "runtime" / "research").ingest_ledgers(ledgers).as_dict()

    def _build_dashboards(self) -> dict[str, Any]:
        from afip.dashboard_ui.dashboard_authority import DashboardAuthority
        result = DashboardAuthority().build_all(
            self.root / "runtime" / "dashboard", project_root=self.root
        )
        return {"status": "READY", "home": str(result.home), "generated_at_utc": utc_now()}

    def _research_status(self, collector: Mapping[str, Any]) -> dict[str, Any]:
        auto_path = self.root / "runtime" / "research" / "automatic_research_status.json"
        obs_path = self.root / "runtime" / "research" / "runtime_observatory_status.json"
        auto = read_json(auto_path)
        obs = read_json(obs_path)
        age = file_age_seconds(obs_path if obs else auto_path)
        stale = age is None or age > max(180, self.interval * 3)
        return {
            "status": "STALE" if stale else str(obs.get("status") or auto.get("status") or "WAITING"),
            "heartbeat_age_seconds": None if age is None else round(age, 1),
            "heartbeat_stale": stale,
            "automatic": auto,
            "observatory": obs,
            "collector": dict(collector),
        }

    def snapshot(self, collector: Mapping[str, Any] | None = None, dashboard: Mapping[str, Any] | None = None) -> dict[str, Any]:
        router = self._router_status()
        profiles = router.get("profiles", []) if isinstance(router.get("profiles"), list) else []
        running = sum(1 for row in profiles if isinstance(row, Mapping) and row.get("runtime_state") == "RUNNING")
        research = self._research_status(collector or {})
        router_running = bool(router.get("router", {}).get("running"))
        overall = "RUNNING" if router_running else "DEGRADED_EXECUTION_BLOCKED"
        if research.get("heartbeat_stale"):
            overall = "DEGRADED" if router_running else "DEGRADED_EXECUTION_AND_RESEARCH"
        payload = {
            "schema_version": SCHEMA_VERSION,
            "status": overall,
            "mode": "DEMO_EXECUTION_ONLY",
            "generated_at_utc": utc_now(),
            "heartbeat_utc": utc_now(),
            "process_id": os.getpid(),
            "execution_authority": "EXISTING_SEQUENTIAL_ROUTER_ONLY",
            "execution_authority_changed": False,
            "order_send_authority_added": False,
            "router": router.get("router", {}),
            "execution_router_running": router_running,
            "execution_allowed": router_running,
            "observability_running": True,
            "profiles": profiles,
            "running_profiles": running,
            "expected_profiles": len(profiles),
            "research": research,
            "dashboard": dict(dashboard or {}),
        }
        atomic_json(self.authority_path, payload)
        return payload

    def run_once(self) -> dict[str, Any]:
        collector: dict[str, Any]
        try:
            collector = self._collect_research()
        except Exception as exc:  # fail observable, not silent
            collector = {"status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
        # Write authority before rendering so every page sees the same cycle.
        self.snapshot(collector, {"status": "BUILDING"})
        try:
            dashboard = self._build_dashboards()
        except Exception as exc:
            dashboard = {"status": "FAILED", "error": f"{type(exc).__name__}: {exc}", "generated_at_utc": utc_now()}
        return self.snapshot(collector, dashboard)

    def run_forever(self) -> int:
        if not self._acquire_supervisor_lock():
            return 3
        self.pid_path.write_text(str(os.getpid()), encoding="utf-8")
        def stop_handler(*_: object) -> None:
            self.stop_requested = True
        signal.signal(signal.SIGTERM, stop_handler)
        if hasattr(signal, "SIGINT"):
            signal.signal(signal.SIGINT, stop_handler)
        router_start: dict[str, Any] = {}
        try:
            router_start = self._start_execution_router()
            while not self.stop_requested:
                result = self.run_once()
                print(json.dumps({
                    "timestamp": result["generated_at_utc"],
                    "status": result["status"],
                    "running_profiles": result["running_profiles"],
                    "research": result["research"].get("status"),
                    "dashboard": result["dashboard"].get("status"),
                    "router_start_status": router_start.get("status", router_start.get("start_result")),
                }, ensure_ascii=False), flush=True)
                deadline = time.monotonic() + self.interval
                while not self.stop_requested and time.monotonic() < deadline:
                    time.sleep(0.5)
        finally:
            try:
                self._stop_execution_router()
            finally:
                self.pid_path.unlink(missing_ok=True)
                self._release_supervisor_lock()
                previous = read_json(self.authority_path)
                atomic_json(self.authority_path, {**previous, "status": "STOPPED", "heartbeat_utc": utc_now(), "process_id": None, "execution_allowed": False})
        return 0

    def start_background(self) -> dict[str, Any]:
        existing = self.pid()
        if existing:
            return {"status": "ALREADY_RUNNING", "pid": existing}
        self.directory.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, "-m", "tools.afip_operational_runtime", "worker", "--interval-seconds", str(self.interval)]
        kwargs: dict[str, Any] = {"cwd": str(self.root), "close_fds": True}
        if os.name == "nt":
            kwargs["creationflags"] = (getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0))
        else:
            kwargs["start_new_session"] = True
        with self.log_path.open("a", encoding="utf-8") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, **kwargs)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if process.poll() is not None:
                return {"status": "FAILED", "reason": f"worker_exited:{process.returncode}"}
            pid = self.pid()
            if pid:
                return {"status": "STARTED", "pid": pid}
            time.sleep(0.25)
        return {"status": "FAILED", "reason": "worker_start_timeout"}

    def pid(self) -> int | None:
        try:
            pid = int(self.pid_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None
        if process_alive(pid):
            return pid
        self.pid_path.unlink(missing_ok=True)
        return None

    def stop(self) -> dict[str, Any]:
        pid = self.pid()
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
            deadline = time.monotonic() + 15
            while self.pid() and time.monotonic() < deadline:
                time.sleep(0.25)
        return {"status": "STOPPED", "pid": self.pid()}
