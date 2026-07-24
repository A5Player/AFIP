"""Passive AFIP startup/control-center status projection.

This module never starts trading, research, MT5, or dashboard processes.  It only
records deterministic observability state and projects existing runtime files.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "afip-control-center.v1"
STAGES = (
    "INITIALIZING",
    "VALIDATING_CONFIGURATION",
    "LOADING_PROFILE_CONFIGURATION",
    "CHECKING_RUNTIME_DIRECTORIES",
    "CHECKING_MT5_TERMINALS",
    "CHECKING_MARKET_DATA",
    "CHECKING_RESEARCH_STORAGE",
    "CHECKING_EXECUTION_AUTHORITY",
    "BUILDING_DASHBOARDS",
    "READY",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}


def atomic_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)
    return path


@dataclass(frozen=True)
class StartupStatus:
    schema_version: str
    status: str
    current_stage: str
    progress_percent: float
    started_at: str
    updated_at: str
    completed_at: str | None
    elapsed_seconds: float
    stages_total: int
    stages_completed: int
    current_message: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    execution_authority_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["warnings"] = list(self.warnings)
        value["errors"] = list(self.errors)
        return value


class ControlCenterRuntime:
    """Read-only projection over existing AFIP runtime artifacts."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.root = Path(project_root).resolve()
        self.directory = self.root / "runtime" / "control_center"
        self.status_path = self.directory / "startup_status.json"
        self.events_path = self.directory / "startup_events.jsonl"

    def write_startup(self, stage: str, *, status: str = "RUNNING", message: str = "", warnings: tuple[str, ...] = (), errors: tuple[str, ...] = ()) -> StartupStatus:
        stage = stage.upper().strip()
        if stage not in STAGES and stage not in {"DEGRADED", "FAILED", "STOPPED"}:
            raise ValueError(f"unsupported startup stage: {stage}")
        previous = read_json(self.status_path)
        now = utc_now()
        started = str(previous.get("started_at") or now)
        completed = STAGES.index(stage) + 1 if stage in STAGES else int(previous.get("stages_completed", 0) or 0)
        final_status = status.upper().strip()
        if errors:
            final_status = "FAILED"
        elif stage == "READY" and warnings:
            final_status = "DEGRADED"
        elif stage == "READY":
            final_status = "READY"
        progress = round(min(100.0, completed / len(STAGES) * 100.0), 2)
        value = StartupStatus(
            SCHEMA_VERSION, final_status, stage, progress, started, now,
            now if final_status in {"READY", "DEGRADED", "FAILED", "STOPPED"} else None,
            0.0, len(STAGES), completed, message or stage.replace("_", " ").title(),
            tuple(warnings), tuple(errors), False,
        )
        atomic_json(self.status_path, value.as_dict())
        self.directory.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"timestamp": now, "stage": stage, "status": final_status, "message": value.current_message}, ensure_ascii=False, sort_keys=True) + "\n")
        return value

    def snapshot(self) -> dict[str, Any]:
        startup = read_json(self.status_path)
        integration = read_json(self.root / "runtime" / "final_integration_status.json")
        research = read_json(self.root / "runtime" / "research" / "automatic_research_status.json")
        if not research:
            research = read_json(self.root / "runtime" / "research" / "research_engine_status.json")
        dashboard = read_json(self.root / "runtime" / "dashboard" / "dashboard_monitor_status.json")
        profiles: list[dict[str, Any]] = []
        for profile_id in ("p1", "p2", "p3", "p4"):
            base = self.root / "runtime" / "profiles" / profile_id
            data = read_json(base / "demo_execution_state.json") or read_json(base / "mt5_health.json")
            login = str(data.get("login") or data.get("account") or "")
            if login:
                data["login"] = ("*" * max(0, len(login) - 4)) + login[-4:]
            data["profile_id"] = profile_id.upper()
            profiles.append(data)
        return {
            "schema_version": SCHEMA_VERSION,
            "generated_at": utc_now(),
            "startup": startup,
            "final_integration": integration,
            "research": research,
            "dashboard": dashboard,
            "profiles": profiles,
            "execution_authority_changed": False,
            "execution_authority": "EXISTING_AFIP_RUNTIME_ONLY",
        }
