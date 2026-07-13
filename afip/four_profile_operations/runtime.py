"""Four-profile locked-simulation operations for AFIP Version 1.0.

Operational configuration only. This module never logs in to MT5, sends an order,
or enables direct/live execution. Credentials are read from environment variables
at runtime and are never persisted by this module.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import subprocess
import signal
from typing import Any, Iterable, Mapping

LOCKED_EXECUTION = "LOCKED_SIMULATION_ONLY"
NO_ORDER_SENT = "NO_ORDER_SENT"


@dataclass(frozen=True)
class ProfileOperationalConfig:
    profile_id: str
    profile_name: str
    enabled: bool
    launch_mt5: bool
    mt5_folder: Path
    mt5_terminal: Path
    broker: str
    server: str
    symbol: str
    login_env: str
    password_env: str
    runtime_directory: Path
    database_path: Path
    logs_directory: Path
    dashboard_path: Path
    learning_directory: Path
    knowledge_directory: Path
    statistics_directory: Path
    execution: str = LOCKED_EXECUTION
    direct_execution: bool = False
    live_execution: bool = False

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ProfileOperationalConfig":
        return cls(
            profile_id=str(raw["profile_id"]).strip().upper(),
            profile_name=str(raw["profile_name"]).strip(),
            enabled=bool(raw.get("enabled", False)),
            launch_mt5=bool(raw.get("launch_mt5", False)),
            mt5_folder=Path(str(raw["mt5_folder"])),
            mt5_terminal=Path(str(raw.get("mt5_terminal") or Path(str(raw["mt5_folder"])) / "terminal64.exe")),
            broker=str(raw.get("broker", "XM")).strip().upper(),
            server=str(raw["server"]).strip(),
            symbol=str(raw.get("symbol", "GOLD#")).strip().upper(),
            login_env=str(raw["login_env"]).strip(),
            password_env=str(raw["password_env"]).strip(),
            runtime_directory=Path(str(raw["runtime_directory"])),
            database_path=Path(str(raw["database_path"])),
            logs_directory=Path(str(raw["logs_directory"])),
            dashboard_path=Path(str(raw["dashboard_path"])),
            learning_directory=Path(str(raw["learning_directory"])),
            knowledge_directory=Path(str(raw["knowledge_directory"])),
            statistics_directory=Path(str(raw["statistics_directory"])),
            execution=str(raw.get("execution", LOCKED_EXECUTION)).strip().upper(),
            direct_execution=bool(raw.get("direct_execution", False)),
            live_execution=bool(raw.get("live_execution", False)),
        )

    @property
    def login(self) -> str:
        return os.environ.get(self.login_env, "").strip()

    @property
    def password_configured(self) -> bool:
        return bool(os.environ.get(self.password_env, ""))

    @property
    def masked_login(self) -> str:
        value = self.login
        return "NOT_CONFIGURED" if not value else f"****{value[-4:]}"

    def validate_policy(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.broker != "XM": errors.append("broker_must_be_xm")
        if self.symbol != "GOLD#": errors.append("symbol_must_be_gold_hash")
        if self.execution != LOCKED_EXECUTION: errors.append("execution_must_remain_locked_simulation_only")
        if self.direct_execution: errors.append("direct_execution_must_be_false")
        if self.live_execution: errors.append("live_execution_must_be_false")
        return tuple(errors)

    def status_record(self) -> dict[str, Any]:
        policy_errors = self.validate_policy()
        return {
            "profile_id": self.profile_id,
            "profile_name": self.profile_name,
            "enabled": self.enabled,
            "status": "READY" if self.enabled and not policy_errors else ("STOPPED" if not self.enabled else "BLOCKED"),
            "broker": self.broker,
            "server": self.server,
            "symbol": self.symbol,
            "account": self.masked_login,
            "credentials_configured": bool(self.login and self.password_configured),
            "mt5_folder": str(self.mt5_folder),
            "mt5_terminal": str(self.mt5_terminal),
            "launch_mt5": self.launch_mt5,
            "runtime": str(self.runtime_directory),
            "database": str(self.database_path),
            "logs": str(self.logs_directory),
            "dashboard": str(self.dashboard_path),
            "learning": str(self.learning_directory),
            "knowledge": str(self.knowledge_directory),
            "statistics": str(self.statistics_directory),
            "execution": LOCKED_EXECUTION,
            "order_status": NO_ORDER_SENT,
            "direct_execution": False,
            "live_execution": False,
            "waiting_reason": "Profile disabled by operator" if not self.enabled else (", ".join(policy_errors) if policy_errors else "Waiting for locked simulation runtime start"),
        }


@dataclass(frozen=True)
class FourProfileReport:
    status: str
    profiles: tuple[dict[str, Any], ...]
    validation_errors: tuple[str, ...]
    execution: str = LOCKED_EXECUTION
    order_status: str = NO_ORDER_SENT
    direct_execution: bool = False
    live_execution: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class FourProfileOperationalRuntime:
    def __init__(self, config_path: str | Path = "config/four_profile_demo.json") -> None:
        self.config_path = Path(config_path)

    def load(self) -> tuple[ProfileOperationalConfig, ...]:
        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        return tuple(ProfileOperationalConfig.from_mapping(item) for item in payload["profiles"])

    @staticmethod
    def _duplicates(profiles: Iterable[ProfileOperationalConfig], attribute: str) -> list[str]:
        seen: dict[str, str] = {}
        duplicates: list[str] = []
        for profile in profiles:
            value = str(getattr(profile, attribute)).casefold()
            if value in seen:
                duplicates.append(f"duplicate_{attribute}:{seen[value]}:{profile.profile_id}")
            else:
                seen[value] = profile.profile_id
        return duplicates

    def validate(self, profiles: tuple[ProfileOperationalConfig, ...] | None = None) -> tuple[str, ...]:
        items = profiles or self.load()
        errors: list[str] = []
        if len(items) != 4: errors.append("exactly_four_profiles_required")
        ids = [p.profile_id for p in items]
        if set(ids) != {"P1", "P2", "P3", "P4"}: errors.append("profile_ids_must_be_p1_to_p4")
        for item in items:
            errors.extend(f"{item.profile_id}:{error}" for error in item.validate_policy())
        for field in ("mt5_folder", "mt5_terminal", "runtime_directory", "database_path", "logs_directory", "dashboard_path", "learning_directory", "knowledge_directory", "statistics_directory"):
            errors.extend(self._duplicates(items, field))
        configured_logins: dict[str, str] = {}
        for item in items:
            if item.login:
                if item.login in configured_logins:
                    errors.append(f"duplicate_account:{configured_logins[item.login]}:{item.profile_id}")
                configured_logins[item.login] = item.profile_id
        return tuple(errors)

    def prepare_isolation(self, selected: Iterable[str] | None = None) -> FourProfileReport:
        profiles = self.load()
        selected_ids = {value.upper() for value in selected} if selected else {p.profile_id for p in profiles if p.enabled}
        errors = self.validate(profiles)
        if not errors:
            for profile in profiles:
                if profile.profile_id not in selected_ids:
                    continue
                profile.runtime_directory.mkdir(parents=True, exist_ok=True)
                profile.database_path.parent.mkdir(parents=True, exist_ok=True)
                profile.logs_directory.mkdir(parents=True, exist_ok=True)
                profile.dashboard_path.parent.mkdir(parents=True, exist_ok=True)
                profile.learning_directory.mkdir(parents=True, exist_ok=True)
                profile.knowledge_directory.mkdir(parents=True, exist_ok=True)
                profile.statistics_directory.mkdir(parents=True, exist_ok=True)
        records = tuple(profile.status_record() for profile in profiles)
        return FourProfileReport("READY" if not errors else "BLOCKED", records, errors)

    def launch_mt5(self, selected: Iterable[str] | None = None) -> FourProfileReport:
        report = self.prepare_isolation(selected)
        if report.validation_errors:
            return report
        selected_ids = {value.upper() for value in selected} if selected else None
        for profile in self.load():
            if not profile.enabled or not profile.launch_mt5:
                continue
            if selected_ids is not None and profile.profile_id not in selected_ids:
                continue
            if not profile.mt5_terminal.exists():
                continue
            subprocess.Popen([str(profile.mt5_terminal), "/portable"], cwd=str(profile.mt5_folder))
        return report

class FourProfileSupervisor:
    """Starts and stops isolated locked-simulation worker processes per profile."""
    def __init__(self, config_path: str | Path = "config/four_profile_demo.json") -> None:
        self.operations = FourProfileOperationalRuntime(config_path)

    @staticmethod
    def _pid_path(profile: ProfileOperationalConfig) -> Path:
        return profile.runtime_directory / "runner.pid"

    @staticmethod
    def _worker_command(profile: ProfileOperationalConfig) -> list[str]:
        import sys
        code = (
            "from pathlib import Path; "
            "from afip.locked_simulation_runtime import LockedSimulationConfig, LockedSimulationRunner; "
            f"LockedSimulationRunner(LockedSimulationConfig(runtime_directory=Path({str(profile.runtime_directory)!r}))).run()"
        )
        return [sys.executable, "-c", code]

    def start(self, selected: Iterable[str] | None = None) -> FourProfileReport:
        report = self.operations.prepare_isolation(selected)
        if report.validation_errors:
            return report
        selected_ids = {value.upper() for value in selected} if selected else None
        for profile in self.operations.load():
            if not profile.enabled or (selected_ids is not None and profile.profile_id not in selected_ids):
                continue
            pid_path = self._pid_path(profile)
            if pid_path.exists():
                try:
                    os.kill(int(pid_path.read_text(encoding="utf-8").strip()), 0)
                    continue
                except (OSError, ValueError):
                    pid_path.unlink(missing_ok=True)
            log_path = profile.logs_directory / "locked_simulation_runner.log"
            with log_path.open("a", encoding="utf-8") as log:
                process = subprocess.Popen(self._worker_command(profile), stdout=log, stderr=subprocess.STDOUT, cwd=str(Path.cwd()))
            pid_path.write_text(str(process.pid), encoding="utf-8")
        return self.status()

    def stop(self, selected: Iterable[str] | None = None) -> FourProfileReport:
        selected_ids = {value.upper() for value in selected} if selected else None
        for profile in self.operations.load():
            if selected_ids is not None and profile.profile_id not in selected_ids:
                continue
            pid_path = self._pid_path(profile)
            if not pid_path.exists():
                continue
            try:
                os.kill(int(pid_path.read_text(encoding="utf-8").strip()), signal.SIGTERM)
            except (OSError, ValueError):
                pass
            pid_path.unlink(missing_ok=True)
        return self.status()

    def restart(self, selected: Iterable[str] | None = None) -> FourProfileReport:
        self.stop(selected)
        return self.start(selected)

    def status(self) -> FourProfileReport:
        profiles = self.operations.load()
        errors = self.operations.validate(profiles)
        records: list[dict[str, Any]] = []
        for profile in profiles:
            record = profile.status_record()
            pid_path = self._pid_path(profile)
            running = False
            pid = None
            if pid_path.exists():
                try:
                    pid = int(pid_path.read_text(encoding="utf-8").strip())
                    os.kill(pid, 0)
                    running = True
                except (OSError, ValueError):
                    pid_path.unlink(missing_ok=True)
            health_path = profile.runtime_directory / "mt5_health.json"
            mt5_health = {}
            if health_path.exists():
                try:
                    mt5_health = json.loads(health_path.read_text(encoding="utf-8"))
                except (OSError, ValueError, TypeError):
                    mt5_health = {}
            record.update({
                "runtime_state": "RUNNING" if running else "STOPPED",
                "pid": pid if running else None,
                "mt5_connection": mt5_health.get("connection_status", "NOT_CHECKED"),
                "latency_ms": mt5_health.get("latency_ms"),
                "reconnect_attempts": mt5_health.get("reconnect_attempts", 0),
                "mt5_reason": mt5_health.get("reason", "MT5 health check not run"),
            })
            records.append(record)
        return FourProfileReport("READY" if not errors else "BLOCKED", tuple(records), errors)
