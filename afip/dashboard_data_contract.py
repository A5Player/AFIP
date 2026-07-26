"""AFIP V1 read-only dashboard data contract.

Consolidates existing runtime evidence into one atomic JSON snapshot.  It never
initializes MT5, calculates trading authority, or sends orders.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "AFIP_V1_DASHBOARD_DATA_CONTRACT_V1"
CONTRACT_PATH = Path("runtime/dashboard/dashboard_runtime.json")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}


def _modified(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    except OSError:
        return None


def _source(root: Path, relative: str, *, stale_after_seconds: int) -> dict[str, Any]:
    path = root / relative
    data = _read(path)
    modified = _modified(path)
    age = max(0, int((_now() - modified).total_seconds())) if modified else None
    producer = data.get("producer") or data.get("generated_by") or data.get("authority") or "NOT_RECORDED"
    pid = data.get("pid") or data.get("process_id") or "NOT_RECORDED"
    execution_mode = data.get("execution_mode") or data.get("execution") or "NOT_RECORDED"
    return {
        "path": relative.replace("\\", "/"),
        "exists": path.is_file(),
        "readable": bool(data),
        "modified_at_utc": _iso(modified) if modified else None,
        "age_seconds": age,
        "stale_after_seconds": stale_after_seconds,
        "fresh": age is not None and age <= stale_after_seconds,
        "current_state": "FRESH" if age is not None and age <= stale_after_seconds else "STALE" if path.is_file() else "NOT_GENERATED",
        "producer": producer,
        "pid": pid,
        "execution_mode": execution_mode,
        "data": data,
    }


def _merge(*values: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for value in values:
        merged.update(dict(value))
    return merged


def _profile_from_integration(integration: Mapping[str, Any], profile_id: str) -> dict[str, Any]:
    trading = integration.get("trading_runtime") if isinstance(integration.get("trading_runtime"), Mapping) else {}
    profiles = trading.get("profiles") if isinstance(trading.get("profiles"), list) else []
    for row in profiles:
        if isinstance(row, Mapping) and str(row.get("profile_id", "")).upper() == profile_id:
            return dict(row)
    return {}


def build_dashboard_contract(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root)
    generated = _now()
    # Refresh the sole process-observation source in passive mode. This call
    # never initializes, logs in, reconnects, or launches MT5.
    passive_profiles: dict[str, dict[str, Any]] = {}
    try:
        from afip.four_profile_operations.mt5_connection import MT5MultiTerminalConnectionManager
        passive_report = MT5MultiTerminalConnectionManager(root / "config/four_profile_demo.json").check(
            reconnect_attempts=0, active=False
        )
        passive_profiles = {
            str(item.get("profile_id", "")).upper(): dict(item)
            for item in passive_report.get("profiles", ())
            if isinstance(item, Mapping)
        }
    except Exception:
        passive_profiles = {}
    config_source = _source(root, "config/four_profile_demo.json", stale_after_seconds=31_536_000)
    integration_source = _source(root, "runtime/final_integration_status.json", stale_after_seconds=120)
    router_source = _source(root, "runtime/execution/sequential_router_status.json", stale_after_seconds=120)
    research_source = _source(root, "runtime/research/automatic_research_status.json", stale_after_seconds=86_400)
    monitor_source = _source(root, "runtime/dashboard/dashboard_monitor_status.json", stale_after_seconds=120)

    config = config_source["data"]
    integration = integration_source["data"]
    rows: list[dict[str, Any]] = []
    for cfg in config.get("profiles", []):
        if not isinstance(cfg, Mapping):
            continue
        pid = str(cfg.get("profile_id", "")).upper()
        runtime_dir = str(cfg.get("runtime_directory", f"runtime/profiles/{pid.lower()}"))
        health_source = _source(root, f"{runtime_dir}/mt5_health.json", stale_after_seconds=120)
        status_source = _source(root, f"{runtime_dir}/status.json", stale_after_seconds=120)
        execution_source = _source(root, f"{runtime_dir}/demo_execution_state.json", stale_after_seconds=120)
        integration_row = _profile_from_integration(integration, pid)
        row = _merge(cfg, integration_row, health_source["data"], status_source["data"], execution_source["data"], passive_profiles.get(pid, {}))
        row["profile_id"] = pid
        row["source_metadata"] = {
            "mt5_health": {k: v for k, v in health_source.items() if k != "data"},
            "profile_status": {k: v for k, v in status_source.items() if k != "data"},
            "execution_state": {k: v for k, v in execution_source.items() if k != "data"},
            "final_integration": {k: v for k, v in integration_source.items() if k != "data"},
        }
        available = [health_source, status_source, execution_source]
        ages = [x["age_seconds"] for x in available if x["age_seconds"] is not None]
        row["data_age_seconds"] = health_source["age_seconds"]
        row["data_fresh"] = bool(health_source["fresh"])
        row["data_status"] = "FRESH" if row["data_fresh"] else "STALE" if health_source["exists"] else "DATA_UNAVAILABLE"
        row["mt5_process_alive"] = bool(row.get("process_alive"))
        row["mt5_monitoring_mode"] = str(row.get("monitoring_mode", "UNKNOWN"))
        row["connection_evidence_fresh"] = bool(health_source["fresh"])
        row["financial_evidence"] = str(row.get("evidence_kind", "DATA_UNAVAILABLE"))
        snapshot_age = row.get("snapshot_age_seconds")
        try:
            snapshot_age_value = int(snapshot_age) if snapshot_age is not None else None
        except (TypeError, ValueError):
            snapshot_age_value = None
        has_financial_snapshot = any(
            row.get(key) is not None
            for key in ("balance", "equity", "free_margin", "bid", "ask")
        )
        evidence_kind = str(row.get("evidence_kind", "")).upper()
        connection_status = str(row.get("connection_status", "")).upper()
        row["financial_live"] = (
            evidence_kind == "LIVE"
            and connection_status == "CONNECTED"
            and bool(health_source["fresh"])
        )
        row["financial_snapshot_available"] = bool(has_financial_snapshot)
        if row["financial_live"]:
            row["financial_state"] = "LIVE"
        elif has_financial_snapshot and snapshot_age_value is not None and snapshot_age_value <= 120:
            row["financial_state"] = "RECENT_SNAPSHOT"
        elif has_financial_snapshot:
            row["financial_state"] = "STALE_SNAPSHOT"
        else:
            row["financial_state"] = "DATA_UNAVAILABLE"
        row["dashboard_data_source"] = "AFIP_V1_DASHBOARD_DATA_CONTRACT"
        rows.append(row)

    required = [config_source, integration_source, router_source]
    contract_status = "READY" if config_source["readable"] and rows else "REVIEW"
    if not any(source["fresh"] for source in required if source["exists"]):
        contract_status = "STALE"

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _iso(generated),
        "status": contract_status,
        "policy": {
            "data_source": "REAL_RUNTIME_EVIDENCE_ONLY",
            "dashboard_calculation_authority": False,
            "trading_logic_changed": False,
            "mt5_initialization_allowed": False,
            "order_send_allowed": False,
            "missing_value_policy": "DATA_UNAVAILABLE",
        },
        "profiles": rows,
        "router": router_source["data"],
        "final_integration": integration,
        "research": research_source["data"],
        "dashboard_monitor": monitor_source["data"],
        "sources": {
            "configuration": {k: v for k, v in config_source.items() if k != "data"},
            "final_integration": {k: v for k, v in integration_source.items() if k != "data"},
            "router": {k: v for k, v in router_source.items() if k != "data"},
            "research": {k: v for k, v in research_source.items() if k != "data"},
            "dashboard_monitor": {k: v for k, v in monitor_source.items() if k != "data"},
        },
    }
    from afip.execution_pipeline_dashboard import attach_execution_pipelines
    from afip.order_evidence_dashboard import attach_order_evidence
    payload = attach_execution_pipelines(payload)
    payload = attach_order_evidence(payload)
    from afip.dashboard_state_machine import attach_runtime_truth
    payload = attach_runtime_truth(payload)
    from afip.dashboard_completeness import attach_dashboard_completeness
    payload = attach_dashboard_completeness(payload)
    from afip.dashboard_operations_health import attach_operations_health
    payload = attach_operations_health(payload)
    from afip.runtime_truth import attach_runtime_truth_model
    payload = attach_runtime_truth_model(payload)
    path = root / CONTRACT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    temporary.replace(path)
    return payload


def load_dashboard_contract(root: str | Path = ".", *, rebuild: bool = True) -> dict[str, Any]:
    root = Path(root)
    if rebuild:
        return build_dashboard_contract(root)
    return _read(root / CONTRACT_PATH)
