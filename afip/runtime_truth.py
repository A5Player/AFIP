"""AFIP runtime truth registry and conflict auditor.

Read-only over existing runtime artifacts except for its own certification report.
It does not initialize MT5, start processes, or change execution authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "afip-runtime-truth.v1"


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
    temporary.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    temporary.replace(path)
    return path


DOMAINS: tuple[dict[str, Any], ...] = (
    {
        "domain": "LIFECYCLE",
        "authority": "runtime/control/final_integration/desired_runtime_state.json",
        "compatibility": ("runtime/final_integration_status.json", "runtime/operational/authority.json"),
        "keys": ("desired_state", "status"),
        "owner": "afip.final_integration.runtime",
    },
    {
        "domain": "EXECUTION_ROUTER",
        "authority": "runtime/execution/sequential_router_status.json",
        "compatibility": ("runtime/final_integration_status.json", "runtime/operational/authority.json"),
        "keys": ("state", "running", "pid"),
        "owner": "tools.afip_profile_sequential_execution_router",
    },
    {
        "domain": "PROFILE_EXECUTION",
        "authority": "runtime/profiles/{profile}/demo_execution_state.json",
        "compatibility": ("runtime/profiles/{profile}/status.json", "runtime/dashboard/dashboard_runtime.json"),
        "keys": ("runtime_state", "gateway_status", "order_status", "decision", "confidence"),
        "owner": "afip.demo_execution_gateway.runtime",
        "profiles": ("p1", "p2", "p3", "p4"),
    },
    {
        "domain": "POSITION_CARE",
        "authority": "runtime/profiles/{profile}/production_activation/position_care_status.json",
        "compatibility": (),
        "keys": ("status", "positions_evaluated"),
        "owner": "afip.production_activation_runtime.runtime",
        "profiles": ("p1", "p2", "p3", "p4"),
    },
    {
        "domain": "RESEARCH_COLLECTION",
        "authority": "runtime/research/runtime_collection_summary.json",
        "compatibility": ("runtime/research/automatic_research_status.json", "runtime/research/runtime_observatory_status.json"),
        "keys": ("trade_cases_written", "holding_observations", "exits_recorded"),
        "owner": "afip.research_data_foundation.runtime_collector",
    },
    {
        "domain": "DASHBOARD",
        "authority": "runtime/dashboard/dashboard_monitor_status.json",
        "compatibility": ("runtime/dashboard/dashboard_runtime.json", "runtime/dashboard/production_authority_snapshot.json"),
        "keys": ("updated_at_utc",),
        "owner": "afip.dashboard_ui.dashboard_authority",
    },
)


def _age_seconds(path: Path) -> float | None:
    try:
        return max(0.0, datetime.now(timezone.utc).timestamp() - path.stat().st_mtime)
    except OSError:
        return None


def _extract(payload: Mapping[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: payload.get(key) for key in keys if payload.get(key) not in (None, "")}


def build_runtime_truth(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).resolve()
    rows: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    missing_authorities: list[str] = []

    for spec in DOMAINS:
        profiles = spec.get("profiles") or (None,)
        for profile in profiles:
            authority_rel = str(spec["authority"]).format(profile=profile or "")
            authority_path = root / authority_rel
            authority_payload = read_json(authority_path)
            label = str(spec["domain"]) + (f":{str(profile).upper()}" if profile else "")
            if not authority_payload:
                missing_authorities.append(label)
            authority_values = _extract(authority_payload, tuple(spec["keys"]))
            compat_rows: list[dict[str, Any]] = []
            for compat_template in spec["compatibility"]:
                compat_rel = str(compat_template).format(profile=profile or "")
                compat_path = root / compat_rel
                compat_payload = read_json(compat_path)
                compat_values = _extract(compat_payload, tuple(spec["keys"]))
                def normalized(key: str, value: Any) -> Any:
                    text = str(value or "").strip().upper()
                    if key == "order_status" and text in {"NO_ORDER_SENT", "ORDER_NOT_SENT"}:
                        return "ORDER_NOT_SENT"
                    return value
                authority_mtime = authority_path.stat().st_mtime if authority_path.exists() else 0.0
                compatibility_mtime = compat_path.stat().st_mtime if compat_path.exists() else 0.0
                disagreements = {
                    key: {"authority": authority_values.get(key), "compatibility": compat_values.get(key)}
                    for key in set(authority_values).intersection(compat_values)
                    if compatibility_mtime >= authority_mtime
                    and normalized(key, authority_values.get(key)) != normalized(key, compat_values.get(key))
                }
                if disagreements:
                    conflicts.append({"domain": label, "path": compat_rel, "fields": disagreements})
                compat_rows.append({
                    "path": compat_rel,
                    "exists": bool(compat_payload),
                    "role": "COMPATIBILITY_READ_ONLY",
                    "age_seconds": _age_seconds(compat_path),
                    "conflicting_fields": sorted(disagreements),
                })
            rows.append({
                "domain": label,
                "owner": spec["owner"],
                "authority_path": authority_rel,
                "authority_exists": bool(authority_payload),
                "authority_age_seconds": _age_seconds(authority_path),
                "authority_values": authority_values,
                "compatibility_sources": compat_rows,
                "status": "MISSING_AUTHORITY" if not authority_payload else ("CONFLICT" if any(x["domain"] == label for x in conflicts) else "CERTIFIED"),
            })

    status = "CERTIFIED" if not conflicts and not missing_authorities else "DEGRADED"
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "generated_at_utc": utc_now(),
        "policy": "ONE_WRITER_PER_DOMAIN_COMPATIBILITY_READ_ONLY",
        "execution_authority_changed": False,
        "mt5_initialized": False,
        "order_send_called": False,
        "domains_certified": sum(1 for row in rows if row["status"] == "CERTIFIED"),
        "domains_total": len(rows),
        "conflict_count": len(conflicts),
        "missing_authority_count": len(missing_authorities),
        "missing_authorities": missing_authorities,
        "conflicts": conflicts,
        "domains": rows,
    }
    atomic_json(root / "runtime" / "certification" / "runtime_truth.json", report)
    return report


# Backward-compatible per-profile dashboard truth API.  This coexists with
# the repository-wide registry above; it is intentionally read-only.
def _upper(value: Any, default: str = "DATA_UNAVAILABLE") -> str:
    text = str(value or "").strip().upper()
    return text or default


def build_profile_truth(profile: Mapping[str, Any]) -> dict[str, Any]:
    process_alive = profile.get("process_alive") is True
    enabled = profile.get("enabled") is not False
    monitor_mode = _upper(profile.get("monitoring_mode"), "PASSIVE")
    raw_connection = _upper(profile.get("connection_status"))
    evidence_kind = _upper(profile.get("evidence_kind"))
    process_state = "DISABLED" if not enabled else ("RUNNING" if process_alive else "STOPPED")
    if monitor_mode in {"ACTIVE", "EXISTING_RUNTIME_SESSION_READ_ONLY"} and raw_connection == "CONNECTED":
        session_state = "CONNECTED"
    elif process_alive:
        session_state = "NOT_VERIFIED_PASSIVE"
    else:
        session_state = "DISCONNECTED"
    broker_session_state = "CONNECTED" if session_state == "CONNECTED" else ("DISCONNECTED" if session_state == "DISCONNECTED" else "NOT_VERIFIED")
    has_financial = any(profile.get(k) is not None for k in ("balance", "equity", "free_margin", "bid", "ask"))
    try:
        age = int(profile.get("snapshot_age_seconds")) if profile.get("snapshot_age_seconds") is not None else None
    except (TypeError, ValueError):
        age = None
    if monitor_mode in {"ACTIVE", "EXISTING_RUNTIME_SESSION_READ_ONLY"} and raw_connection == "CONNECTED" and evidence_kind == "LIVE":
        financial_state = "LIVE"
    elif has_financial and age is not None and age <= 120:
        financial_state = "RECENT_SNAPSHOT"
    elif has_financial:
        financial_state = "STALE_SNAPSHOT"
    else:
        financial_state = "DATA_UNAVAILABLE"
    has_normalized_truth = isinstance(profile.get("runtime_truth"), Mapping)
    normalized = profile.get("runtime_truth") if has_normalized_truth else {}
    runtime_state = _upper(normalized.get("runtime_current") or profile.get("runtime_state") or profile.get("status"), "STOPPED")
    runtime_evidence_fresh = bool(normalized.get("runtime_evidence_fresh")) if has_normalized_truth else True
    execution_state = _upper(profile.get("execution") or profile.get("execution_authority"), "DATA_UNAVAILABLE")
    if not enabled:
        operational_state, reason = "DISABLED", "profile_disabled"
    elif runtime_state == "RUNNING" and runtime_evidence_fresh and process_alive:
        operational_state, reason = "RUNNING", "afip_runtime_and_mt5_process_running"
    elif runtime_state == "RUNNING" and runtime_evidence_fresh and not process_alive:
        if has_normalized_truth:
            operational_state, reason = "WAITING_FOR_MT5", "afip_runtime_running_waiting_for_user_started_mt5"
        else:
            operational_state, reason = "DEGRADED", "afip_runtime_running_but_mt5_process_stopped"
    elif runtime_state == "STALE":
        operational_state, reason = "STALE", "runtime_record_exists_but_heartbeat_is_stale"
    elif process_alive:
        operational_state, reason = "IDLE", "mt5_process_running_but_afip_runtime_not_running"
    else:
        operational_state, reason = "STOPPED", "no_active_afip_runtime"
    return {
        "schema_version": "AFIP_V1_RUNTIME_TRUTH_V1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile_id": str(profile.get("profile_id", "UNKNOWN")).upper(),
        "process_state": process_state, "process_alive": process_alive,
        "session_state": session_state, "broker_session_state": broker_session_state,
        "financial_state": financial_state, "runtime_state": runtime_state,
        "runtime_evidence_fresh": runtime_evidence_fresh, "execution_state": execution_state,
        "operational_state": operational_state, "reason": reason,
        "monitoring_mode": monitor_mode, "connection_status": raw_connection,
        "evidence_kind": evidence_kind, "snapshot_age_seconds": age,
        "financial_live": financial_state == "LIVE",
        "financial_snapshot_available": financial_state in {"RECENT_SNAPSHOT", "STALE_SNAPSHOT"},
        "observation_current": True,
    }


def attach_runtime_truth_model(contract: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(contract)
    rows = []
    for value in payload.get("profiles", ()):
        if not isinstance(value, Mapping):
            continue
        row = dict(value); truth = build_profile_truth(row)
        row["authoritative_runtime_truth"] = truth
        for key in ("process_alive", "process_state", "session_state", "broker_session_state", "financial_state", "financial_live", "financial_snapshot_available", "operational_state"):
            row[key] = truth[key]
        row["mt5_process_alive"] = truth["process_alive"]
        row["operational_reason"] = truth["reason"]
        row["connection_evidence_fresh"] = truth["observation_current"]
        rows.append(row)
    payload["profiles"] = rows
    payload["runtime_truth_model"] = {"schema_version": "AFIP_V1_RUNTIME_TRUTH_V1", "generated_at_utc": datetime.now(timezone.utc).isoformat(), "policy": "SINGLE_READ_ONLY_AUTHORITY", "mt5_initialization_allowed": False, "order_send_allowed": False}
    return payload
