"""AFIP V1 production runtime authority.

Read-only dashboard consolidation plus safe cleanup of stale process artefacts.
This module never initializes MetaTrader5 and never sends orders.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

RUNTIME_AUTHORITY_VERSION = "AFIP_V1_PRODUCTION_RUNTIME_AUTHORITY_V1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(payload), indent=2, default=str), encoding="utf-8")
    temporary.replace(path)
    return path


def process_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    if pid == os.getpid():
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def lock_owner(lock_path: Path) -> dict[str, Any]:
    """Read both legacy token locks and JSON ownership locks."""
    try:
        text = lock_path.read_text(encoding="utf-8").strip()
    except OSError:
        return {}
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        parts = text.split(":", 2)
        try:
            pid = int(parts[1]) if len(parts) > 1 else None
        except ValueError:
            pid = None
        return {"profile_id": parts[0] if parts else "UNKNOWN", "pid": pid, "token": text}


def reclaim_stale_lock(lock_path: Path, maximum_age_seconds: float = 180.0) -> bool:
    """Remove a routing lock only when its owner is dead and the lock is old."""
    if not lock_path.exists():
        return False
    owner = lock_owner(lock_path)
    pid = owner.get("pid")
    try:
        age = max(0.0, datetime.now().timestamp() - lock_path.stat().st_mtime)
    except OSError:
        return False
    if process_alive(int(pid) if pid not in (None, "") else None):
        return False
    if age < maximum_age_seconds:
        return False
    try:
        lock_path.unlink()
        return True
    except OSError:
        return False


def clean_stale_runtime(root: str | Path = ".") -> dict[str, Any]:
    """Clean only provably stale control files; preserve financial/research evidence."""
    root = Path(root)
    removed: list[str] = []
    lock = root / "runtime" / "execution" / "account_routing.lock"
    if reclaim_stale_lock(lock):
        removed.append(str(lock))

    pid_file = root / "runtime" / "execution" / "sequential_router.pid"
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            pid = None
        if not process_alive(pid):
            try:
                pid_file.unlink()
                removed.append(str(pid_file))
            except OSError:
                pass

    for temporary in (root / "runtime").rglob("*.tmp") if (root / "runtime").exists() else ():
        try:
            age = datetime.now().timestamp() - temporary.stat().st_mtime
            if age > 300:
                temporary.unlink()
                removed.append(str(temporary))
        except OSError:
            pass

    report = {
        "schema_version": RUNTIME_AUTHORITY_VERSION,
        "status": "READY",
        "removed_stale_control_files": removed,
        "removed_count": len(removed),
        "updated_at_utc": utc_now(),
    }
    atomic_write_json(root / "runtime" / "execution" / "runtime_cleanup_status.json", report)
    return report


def _profile_runtime(root: Path, runtime_directory: Path) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    preferred = (
        "mt5_health.json", "demo_execution_state.json", "runtime_state.json",
        "profile_state.json", "decision_state.json", "position_state.json",
    )
    for name in preferred:
        merged.update(read_json(root / runtime_directory / name))
    return merged


def build_dashboard_snapshot(
    profiles: Iterable[Mapping[str, Any]] = (), root: str | Path = "."
) -> dict[str, Any]:
    """Build one deterministic, read-only dashboard data snapshot."""
    root = Path(root)
    config = read_json(root / "config" / "four_profile_demo.json")
    supplied = {str(x.get("profile_id", "")).upper(): dict(x) for x in profiles}
    rows: list[dict[str, Any]] = []
    for cfg in config.get("profiles", []):
        if not isinstance(cfg, dict):
            continue
        pid = str(cfg.get("profile_id", "")).upper()
        runtime_dir = Path(str(cfg.get("runtime_directory", f"runtime/profiles/{pid.lower()}")))
        row = dict(cfg)
        row.update(_profile_runtime(root, runtime_dir))
        row.update(supplied.get(pid, {}))
        row["profile_id"] = pid
        row["execution_pipeline"] = "UNIFIED_PROCESS_ISOLATED_MT5"
        row["research_pipeline"] = "RESEARCH_RUNTIME_AND_DATA_LAKE"
        rows.append(row)

    router = read_json(root / "runtime" / "execution" / "sequential_router_status.json")
    cleanup = read_json(root / "runtime" / "execution" / "runtime_cleanup_status.json")
    snapshot = {
        "schema_version": RUNTIME_AUTHORITY_VERSION,
        "generated_at_utc": utc_now(),
        "profiles": rows,
        "router": router,
        "runtime_cleanup": cleanup,
        "execution_profiles": [row["profile_id"] for row in rows if row.get("execution_enabled")],
        "dashboard_data_policy": "REAL_SOURCE_ONLY",
        "placeholder_financial_data": False,
    }
    atomic_write_json(root / "runtime" / "dashboard" / "production_authority_snapshot.json", snapshot)
    return snapshot
