from __future__ import annotations

from dataclasses import asdict, dataclass
import os
import signal
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .architecture import ArchitectureRegistry
from .io import atomic_json, pid_running, read_json, utc_now


@dataclass(frozen=True)
class FinalIntegrationStatus:
    schema_version: str
    status: str
    updated_at_utc: str
    trading_runtime: dict[str, Any]
    research_runtime: dict[str, Any]
    dashboard: dict[str, Any]
    architecture: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["architecture"]["runtime_authorities"] = list(
            data["architecture"].get("runtime_authorities", ())
        )
        data["historical_data_lake"] = data["architecture"].get(
            "historical_data_lake",
            {
                "incremental_index": "runtime/research/research_file_index.json",
                "execution_authority": False,
            },
        )
        return data


DASHBOARD_REFRESH_CONTRACT = {'refresh_interval_seconds':10,'full_refresh_interval_seconds':60}

class FinalIntegrationRuntime:
    """Single operational authority with supervised service continuity.

    The continuity watchdog only restores AFIP processes that were explicitly
    placed in the RUNNING desired state by START_AFIP. It never opens MT5,
    changes trading policy, or bypasses execution gates.
    """

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()
        self.control = self.root / "runtime/control/final_integration"
        self.logs = self.root / "runtime/logs"
        self.status_path = self.root / "runtime/final_integration_status.json"
        self.research_pid_path = self.control / "research_runtime.pid"
        self.dashboard_pid_path = self.control / "dashboard_monitor.pid"
        self.watchdog_pid_path = self.control / "runtime_watchdog.pid"
        self.research_stop_flag = self.control / "stop_research_runtime.flag"
        self.watchdog_stop_flag = self.control / "stop_runtime_watchdog.flag"
        self.desired_state_path = self.control / "desired_runtime_state.json"
        self.watchdog_status_path = self.control / "runtime_watchdog_status.json"
        self._service_markers = {
            "research": "tools.afip_final_integration research-forever",
            "dashboard": "tools.afip_dashboard_monitor",
            "watchdog": "tools.afip_runtime_continuity_watchdog",
            "router": "tools.afip_profile_sequential_execution_router",
        }

    def _pid(self, path: Path) -> int | None:
        try:
            return int(path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None

    def _desired_state(self) -> str:
        return str(read_json(self.desired_state_path).get("state", "STOPPED")).upper()

    def _write_desired_state(self, state: str, reason: str) -> None:
        atomic_json(
            self.desired_state_path,
            {
                "schema_version": "afip-runtime-desired-state.v1",
                "state": state.upper(),
                "reason": reason,
                "updated_at_utc": utc_now(),
            },
        )

    def _trading(self, command: str) -> dict[str, Any]:
        try:
            cp = subprocess.run(
                [sys.executable, "-m", "tools.afip_demo_execution_control", command],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
            )
            import json

            return (
                json.loads(cp.stdout)
                if cp.stdout.strip()
                else {
                    "status": "ERROR",
                    "returncode": cp.returncode,
                    "stderr": cp.stderr[-2000:],
                }
            )
        except Exception as exc:
            return {"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}"}

    def _process_inventory(self) -> list[dict[str, Any]]:
        """Return AFIP Python processes with PID, parent PID and command line.

        Windows virtual-environment launchers may expose a parent/child pair for
        one logical Python service. Logical identity is therefore determined by
        command-line marker, not by a single PID file.
        """
        rows: list[dict[str, Any]] = []
        if os.name == "nt":
            script = (
                "Get-CimInstance Win32_Process | "
                "Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine } | "
                "Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress"
            )
            try:
                cp = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                    text=True, capture_output=True, check=False, timeout=15,
                )
                value = json.loads(cp.stdout or "[]")
                if isinstance(value, dict):
                    value = [value]
                for item in value if isinstance(value, list) else []:
                    command_line = str(item.get("CommandLine") or "")
                    if str(self.root).lower() not in command_line.lower():
                        continue
                    rows.append({
                        "pid": int(item.get("ProcessId") or 0),
                        "parent_pid": int(item.get("ParentProcessId") or 0),
                        "command_line": command_line,
                    })
            except Exception:
                return []
            return rows

        proc_root = Path("/proc")
        if not proc_root.exists():
            return rows
        for entry in proc_root.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                command_line = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
                if str(self.root) not in command_line:
                    continue
                stat = (entry / "stat").read_text(encoding="utf-8", errors="replace").split()
                rows.append({"pid": int(entry.name), "parent_pid": int(stat[3]), "command_line": command_line})
            except Exception:
                continue
        return rows

    def _service_processes(self, service: str) -> list[dict[str, Any]]:
        marker = self._service_markers[service].lower()
        return [row for row in self._process_inventory() if marker in str(row.get("command_line", "")).lower()]

    def _logical_service_pid(self, service: str) -> int | None:
        rows = self._service_processes(service)
        if not rows:
            return None
        pids = {int(row["pid"]) for row in rows}
        roots = [row for row in rows if int(row.get("parent_pid") or 0) not in pids]
        chosen = min(roots or rows, key=lambda row: int(row["pid"]))
        return int(chosen["pid"])

    def _service_running(self, service: str, pid_path: Path | None = None) -> bool:
        logical_pid = self._logical_service_pid(service)
        if logical_pid:
            if pid_path is not None:
                pid_path.parent.mkdir(parents=True, exist_ok=True)
                pid_path.write_text(str(logical_pid), encoding="utf-8")
            return True
        pid = self._pid(pid_path) if pid_path is not None else None
        return pid_running(pid)

    def _spawn(self, service: str | Path, pid_path: Path | list[str], command: list[str] | str, log_name: str | None = None) -> bool:
        # Backward compatibility: _spawn(pid_path, command, log_name).
        if log_name is None:
            legacy_pid_path = Path(service)
            legacy_command = list(pid_path) if isinstance(pid_path, list) else []
            legacy_log_name = str(command)
            marker = "research" if legacy_pid_path == self.research_pid_path else "dashboard" if legacy_pid_path == self.dashboard_pid_path else "watchdog"
            service, pid_path, command, log_name = marker, legacy_pid_path, legacy_command, legacy_log_name
        if self._service_running(service, pid_path):
            return False
        pid_path.unlink(missing_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        with (self.logs / log_name).open("a", encoding="utf-8") as out:
            kwargs: dict[str, Any] = {
                "cwd": self.root,
                "stdout": out,
                "stderr": subprocess.STDOUT,
            }
            if os.name == "nt":
                kwargs["creationflags"] = (
                    getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                    | getattr(subprocess, "DETACHED_PROCESS", 0)
                    | getattr(subprocess, "CREATE_NO_WINDOW", 0)
                )
            else:
                kwargs["start_new_session"] = True
            proc = subprocess.Popen(command, **kwargs)
        pid_path.write_text(str(proc.pid), encoding="utf-8")
        return True

    def ensure_services(self, include_watchdog: bool = True) -> dict[str, Any]:
        """Restore missing AFIP services only while desired state is RUNNING."""
        self.control.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        if self._desired_state() != "RUNNING":
            return {
                "status": "IDLE",
                "reason": "desired_runtime_state_not_running",
                "actions": [],
            }

        actions: list[str] = []
        self.research_stop_flag.unlink(missing_ok=True)
        self.watchdog_stop_flag.unlink(missing_ok=True)

        if self._spawn(
            "research",
            self.research_pid_path,
            [
                sys.executable,
                "-m",
                "tools.afip_final_integration",
                "research-forever",
                "--root",
                str(self.root),
            ],
            "afip_research_runtime.log",
        ):
            actions.append("research_runtime_started")

        if self._spawn(
            "dashboard",
            self.dashboard_pid_path,
            [
                sys.executable,
                "-m",
                "tools.afip_dashboard_monitor",
                "--root",
                str(self.root),
                '--fast-interval','10',
                '--full-interval','60',
            ],
            "afip_dashboard_monitor.log",
        ):
            actions.append("dashboard_monitor_started")

        trading = self._trading("status")
        router = trading.get("router") if isinstance(trading.get("router"), dict) else {}
        if not bool(router.get("running")):
            trading = self._trading("start-all")
            if trading.get("status") != "BLOCKED":
                actions.append("sequential_router_started")
            else:
                actions.append("sequential_router_blocked")

        if include_watchdog and self._spawn(
            "watchdog",
            self.watchdog_pid_path,
            [
                sys.executable,
                "-m",
                "tools.afip_runtime_continuity_watchdog",
                "--root",
                str(self.root),
                "--interval",
                "10",
            ],
            "afip_runtime_watchdog.log",
        ):
            actions.append("runtime_watchdog_started")

        return {
            "status": "READY" if trading.get("status") != "BLOCKED" else "BLOCKED",
            "reason": "services_checked",
            "actions": actions,
            "trading": trading,
        }

    def start(self) -> FinalIntegrationStatus:
        self.control.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        self._write_desired_state("RUNNING", "start_requested")
        result = self.ensure_services(include_watchdog=True)
        if result.get("status") == "BLOCKED":
            return self.status()
        from .dashboard import UnifiedDashboardAuthority

        UnifiedDashboardAuthority(self.root).build()
        return self.status()

    def _terminate_pid(self, path: Path) -> None:
        pid = self._pid(path)
        if pid_running(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        path.unlink(missing_ok=True)

    def _terminate_service(self, service: str, pid_path: Path) -> None:
        """Terminate every process belonging to one logical AFIP service.

        This deliberately handles orphaned Windows launcher/interpreter pairs
        even when the PID registry is stale or missing.
        """
        rows = self._service_processes(service)
        pids = sorted({int(row["pid"]) for row in rows}, reverse=True)
        if os.name == "nt":
            for pid in pids:
                subprocess.run(
                    ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
                )
        else:
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                except OSError:
                    pass
        self._terminate_pid(pid_path)

    def _write_stopped_snapshot(self, path: Path, **values: Any) -> None:
        previous = read_json(path)
        now = utc_now()
        atomic_json(
            path,
            {
                **previous,
                **values,
                "status": "STOPPED",
                "updated_at_utc": now,
                "heartbeat_utc": now,
                "pid": None,
                "process_id": None,
                "execution_authority": False,
                "order_send_called": False,
            },
        )

    def stop(self) -> FinalIntegrationStatus:
        # Set desired STOPPED before terminating anything so the watchdog cannot
        # recreate a process during an intentional shutdown.
        self._write_desired_state("STOPPED", "stop_requested")
        self.watchdog_stop_flag.parent.mkdir(parents=True, exist_ok=True)
        self.watchdog_stop_flag.write_text(utc_now(), encoding="utf-8")
        self.research_stop_flag.write_text(utc_now(), encoding="utf-8")
        self._trading("stop-all")
        for service, path in (
            ("watchdog", self.watchdog_pid_path),
            ("research", self.research_pid_path),
            ("dashboard", self.dashboard_pid_path),
        ):
            self._terminate_service(service, path)
        time.sleep(1)
        self._write_stopped_snapshot(
            self.root / "runtime/research/research_engine_status.json",
            live_execution_enabled=False,
        )
        self._write_stopped_snapshot(
            self.root / "runtime/research/runtime_observatory_status.json",
            stage="STOPPED",
            current_activity="Research runtime stopped",
        )
        self._write_stopped_snapshot(
            self.root / "runtime/dashboard/dashboard_monitor_status.json",
            cycles=read_json(
                self.root / "runtime/dashboard/dashboard_monitor_status.json"
            ).get("cycles", 0),
            execution_authority=False,
        )
        atomic_json(
            self.watchdog_status_path,
            {
                "schema_version": "afip-runtime-continuity-watchdog.v1",
                "status": "STOPPED",
                "reason": "intentional_stop",
                "updated_at_utc": utc_now(),
                "pid": None,
                "execution_authority": False,
                "order_send_called": False,
            },
        )
        return self.status()

    def status(self) -> FinalIntegrationStatus:
        trading = self._trading("status")
        rpid = self._pid(self.research_pid_path)
        dpid = self._pid(self.dashboard_pid_path)
        wpid = self._pid(self.watchdog_pid_path)
        research_running = self._service_running("research", self.research_pid_path)
        rpid = self._pid(self.research_pid_path)
        engine = read_json(self.root / "runtime/research/research_engine_status.json")
        observatory = read_json(
            self.root / "runtime/research/runtime_observatory_status.json"
        )
        if not research_running:
            engine = {
                **engine,
                "status": "STOPPED",
                "pid": None,
                "process_id": None,
                "live_execution_enabled": False,
                "order_send_called": False,
            }
            observatory = {
                **observatory,
                "status": "STOPPED",
                "stage": "STOPPED",
                "current_activity": "Research runtime stopped",
                "pid": None,
                "process_id": None,
                "execution_authority": False,
                "order_send_called": False,
            }
        research = {
            "process_state": "RUNNING" if research_running else "STOPPED",
            "pid": rpid if research_running else None,
            "engine": engine,
            "file_index": read_json(
                self.root / "runtime/research/research_file_index.json"
            ),
            "observatory": observatory,
            "blocks_trading_start": False,
        }
        architecture = ArchitectureRegistry(self.root).inspect().as_dict()
        architecture["runtime_authorities"] = list(
            architecture.get("runtime_authorities", ())
        )
        architecture["execution_authority_in_research"] = False
        dashboard_path = self.root / "runtime/dashboard/afip_dashboard.html"
        dashboard_running = self._service_running("dashboard", self.dashboard_pid_path)
        dpid = self._pid(self.dashboard_pid_path)
        dashboard_status = read_json(
            self.root / "runtime/dashboard/dashboard_monitor_status.json"
        )
        if not dashboard_running:
            dashboard_status = {
                **dashboard_status,
                "status": "STOPPED",
                "pid": None,
                "process_id": None,
                "execution_authority": False,
            }
        dashboard = {
            "authority": "AFIP_SINGLE_PRODUCTION_DASHBOARD",
            "path": "runtime/dashboard/afip_dashboard.html",
            "exists": dashboard_path.exists(),
            "process_state": "RUNNING" if dashboard_running else "STOPPED",
            "pid": dpid if dashboard_running else None,
            "refresh_interval_seconds": 10,
            "fast_refresh_interval_seconds": 10,
            "full_refresh_interval_seconds": 60,
            "background_only": True,
            "execution_authority": False,
            "status": dashboard_status,
            "continuity_watchdog": {
                "process_state": "RUNNING" if self._service_running("watchdog", self.watchdog_pid_path) else "STOPPED",
                "pid": self._pid(self.watchdog_pid_path) if self._service_running("watchdog", self.watchdog_pid_path) else None,
                "desired_state": self._desired_state(),
                "status": read_json(self.watchdog_status_path),
            },
        }
        router = trading.get("router") if isinstance(trading.get("router"), dict) else None
        if router is not None and not router.get("running"):
            trading = {
                **trading,
                "router": {**router, "pid": None, "state": "STOPPED", "running": False},
            }
        active_trading = any(
            x.get("runtime_state") == "RUNNING"
            for x in trading.get("profiles", [])
            if isinstance(x, dict)
        )
        active_research = research["process_state"] == "RUNNING"
        status = "RUNNING" if active_trading or active_research else "STOPPED"
        historical_data_lake = {
            "incremental_index": "runtime/research/research_file_index.json",
            "execution_authority": False,
        }
        architecture["historical_data_lake"] = historical_data_lake
        value = FinalIntegrationStatus(
            "afip-final-integration.v4",
            status,
            utc_now(),
            trading,
            research,
            dashboard,
            architecture,
        )
        payload = value.as_dict()
        payload["historical_data_lake"] = historical_data_lake
        atomic_json(self.status_path, payload)
        return value
